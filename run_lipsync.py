#!/usr/bin/env python3
import argparse
from util import post_request
from schemas.input import INPUT_SCHEMA

def parse_args():
    parser = argparse.ArgumentParser(description='Run lip sync with specified parameters')
    
    # Add required arguments
    parser.add_argument('--source-video', type=str, required=True,
                      help='Path to the source video file')
    parser.add_argument('--source-audio', type=str, required=True,
                      help='Path to the source audio file')
    
    # Add optional arguments with defaults from schema
    parser.add_argument('--face-restore', type=bool, default=INPUT_SCHEMA['face_restore']['default'],
                      help='Whether to restore face quality')
    parser.add_argument('--upscale', type=int, default=INPUT_SCHEMA['upscale']['default'],
                      help='Upscale factor')
    parser.add_argument('--codeformer-fidelity', type=float, 
                      default=INPUT_SCHEMA['codeformer_fidelity']['default'],
                      help='Codeformer fidelity parameter')
    
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    # Create the payload dictionary
    payload = {
        "input": {
            "source_video": args.source_video,
            "source_audio": args.source_audio,
            "face_restore": args.face_restore,
            "upscale": args.upscale,
            "codeformer_fidelity": args.codeformer_fidelity
        }
    }

    post_request(payload)
