import json
import os
import requests
import boto3
from botocore.exceptions import ClientError
from pynico_eros_montin import pynico as pn
import cmrawspy.cmrawspy as ca
import tess.tess as tess
import traceback
result_s3 = os.getenv("ResultsBucketName",'tess-r')
failed_s3 = os.getenv("FailedBucketName",'tess-f')

tess_bin=os.getenv("TESS_BIN",'cpptemperature')

debug=os.getenv("DEBUG",False)

from cmrawspy import cmrawspy as cm

def handler(event, context=None,eventjson=None,jsonoption=None):
    print("eros.montin@gmail.com")
    # start the log
    L = pn.Log("tess",{ "event": event, "context": context })
    # # create a directory for the calculation to be zippedin the end
    O = pn.createRandomTemporaryPathableFromFileName("a.zip")
    O.ensureDirectoryExistence()
    O2 = pn.createRandomTemporaryPathableFromFileName("a.zip")
    O2.appendPathRandom()
    O2.ensureDirectoryExistence()
    outdir=O2.getPath() +'/'
    
    OUT=ca.cmrOutput('TESS',O.getPosition(),outdir)
    OUT.setEvent(event)
    print("event",event)
    print(f"debug {debug}")
    if eventjson != None:
        event=eventjson
    try:
        if jsonoption == None:
            if debug==True:
                jf = "run-job-python/job.json"  
            else:
                job_bucket, job_file_key = cm.getBucketAndKeyIdFromUplaodEvent(event)
                # get the job file from the job bucket
                O.changeBaseName("job.json")
                jf=cm.downloadFileFromS3(job_bucket, job_file_key)
                print(f"bucket_name {job_bucket}")
                print(f"file_key {job_file_key}")
                print(f"job file {jf}")

                L.append(f"bucket_name {job_bucket}")
            
                L.append(f"file_key {job_file_key}")
        
        
        #only for dev
        # jf = "run-job-python/job.json"
            J = pn.Pathable(jf).readJson()
        else:
            J=jsonoption

        L.append("json file read ")
        print("json file read ")

        # copy the task part of mroptimum ui
        pipelineid = J["pipeline"]
        L.append(f"pipelineid {pipelineid}")
        token = J["token"]
        L.append(f"token read {token}")
        print(f"token read {token}")
        OUT.setToken(token)
        OUT.setPipeline(pipelineid)

        T=J["task"]
        L.append(f"task read")
        OPT=T["options"]
        print(f"options read {OPT}")
        MATLAB=J["output"]["matlab"]
        OUT.savematlab=MATLAB
        L.append(f"matlab converter requested {MATLAB}")
        TESS=tess.Tess()
        TESS.binfile=tess_bin
        print(f"tess_bin {tess_bin}") 

        print(OPT)

        if "materialDensity" in T["files"]:
            md=ca.getCMRFile(OPT["materialDensity"])
            TESS.setMaterialDensityMap(md)
            L.append(f"materialDensity read")
            OUT.addAbleFromFilename(filename=md,id=10,name='Material Density',type="input")
        if "mask" in T["files"]:
            mask=ca.getCMRFile(OPT["mask"])
            TESS.setSpace(mask)
            L.append(f"mask read")
            OUT.addAbleFromFilename(filename=mask,id=11,name='Mask',type="input")   

        else:
            L.append("mask not read space set from materialDensity")
            TESS.setSpace(md)
        if "bloodPerfusion" in T["files"]:
            bp=ca.getCMRFile(OPT["bloodPerfusion"])
            TESS.setBloodPerfusionMap(bp)
            L.append(f"bloodPerfusion read")
            OUT.addAbleFromFilename(filename=bp,id=12,name='Blood Perfusion',type="input")  
        if "heatCapacity" in T["files"]:
            hc=ca.getCMRFile(OPT["heatCapacity"])
            TESS.setHeatCapacityMap(hc)
            L.append(f"heatCapacity read")
            OUT.addAbleFromFilename(filename=hc,id=13,name='Heat Capacity',type="input")    
        if "thermalConductivity" in T["files"]:
            tc=ca.getCMRFile(OPT["thermalConductivity"])
            TESS.setThermalConductivityMap(tc)
            L.append(f"thermalConductivity read")
            OUT.addAbleFromFilename(filename=tc,id=14,name='Thermal Conductivity',type="input")
        if "metabolismHeat" in T["files"]:
            mh=ca.getCMRFile(OPT["metabolismHeat"])
            TESS.setMetabolismHeatMap(mh)
            L.append(f"metabolismHeat read")
            OUT.addAbleFromFilename(filename=mh,id=15,name='Metabolism Heat',type="input")
        if "SAR" in T["files"]:
            sar=ca.getCMRFile(OPT["SAR"])
            TESS.setSARMap(sar)
            L.append(f"SAR read")
            OUT.addAbleFromFilename(filename=sar,id=16,name='SAR',type="input")
        if "tOld" in T["files"]:
            to=ca.getCMRFile(OPT["tOld"])
            TESS.setTOldMap(to)
            L.append(f"tOld read")
            OUT.addAbleFromFilename(filename=to,id=17,name='tOld',type="input")
        air =tess.getdfltAir()
        blood =tess.getdfltBlood()
        TESS.setHeatingTime(OPT["heatingtime"])

        L.append(f"heatingtime read")
        for a in OPT["air"].keys():
            if OPT["air"][a] != None:
                air[a]=OPT["air"][a]
        TESS.setAirParameters(air)
        L.append(f"air set")

        for b in OPT["blood"].keys():
            if OPT["blood"][b] != None:
                blood[b]=OPT["blood"][b]

        TESS.setBloodParameters(blood)
        L.append(f"blood set")
        L.append(f"air {air}")
        L.append(f"blood {blood}")
        O=TESS.getOutput()

        print(f"calculation finished")

        OUT.addAble(O,id=0,name='Final Temperature',type="output",basename="temp.nii.gz")
        OUT.setLog(L)
        OUT.setOptions(OPT)
        OUT.setTask(T)
        OUT.exportAndZipResultsToS3(bucket=result_s3,delete=True)
        return {
            'statusCode': 200,
            'body': json.dumps({
                "results":{
                    "key":pipelineid + '.zip',
                    "bucket":result_s3
                }
            })
        }
    
    except Exception as e:
        print(e)
        traceback.print_exc()  # Print the traceback to the console

        L.append(f"error {e}")
        OUT.setLog(L)
        OUT.exportAndZipResultsToS3(bucket=failed_s3)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            }),
        }

    
  

    



if __name__=="__main__":
    J=pn.Pathable("run-job-python/s3job.json").readJson() 
    handler({}, None,jsonoption=J)


    #     return {
    #         'statusCode': 200,
    #         'body': json.dumps({
    #             "results":{
    #                 "key":pipeline_id + '.zip',
    #                 "bucket":RESULTS_BUCKET_NAME
    #             }
    #         })
    #     }

    # except Exception as e:
    #     print(e)
    #     return {
    #         "statusCode": 500,
    #         "body": json.dumps({
    #             "error": str(e)
    #         }),
    #     }
