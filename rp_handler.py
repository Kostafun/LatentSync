import runpod
import time

from scripts.inference import run_inference

def handler(event):
    print(f"Worker Start")
    # input = event['input']
    
    #prompt = input.get('prompt')  
    #seconds = input.get('seconds', 0)  

    # print(f"Received prompt: {prompt}")
    # print(f"Sleeping for {seconds} seconds...")
    
    video_path = run_inference(event)

    
    # Replace the sleep code with your Python function to generate images, text, or run any machine learning workload
    # time.sleep(seconds)  
    
    # return prompt 
    return {"refresh_worker": True, "job_results": {"video_path": video_path}}

if __name__ == '__main__':
    runpod.serverless.start({'handler': handler })
