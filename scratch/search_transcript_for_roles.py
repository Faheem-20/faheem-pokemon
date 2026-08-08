import os
import json

def search_transcript():
    log_dir = r"C:\Users\simha\.gemini\antigravity\brain\80c86ee9-2929-42c6-8cb0-b5e823307d46\.system_generated\logs"
    transcript_path = os.path.join(log_dir, "transcript.jsonl")
    if not os.path.exists(transcript_path):
        transcript_path = os.path.join(log_dir, "transcript_full.jsonl")
        
    if not os.path.exists(transcript_path):
        print("Transcript file not found")
        return
        
    print(f"Searching transcript file: {transcript_path}...")
    
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                step = json.loads(line)
                content = str(step.get("content", ""))
                # Search for mentions of forgot password or role selection in tool_calls or content
                if "forgot" in content.lower() or "role" in content.lower():
                    # Check if it has a write_to_file or replace_file_content tool call
                    tool_calls = step.get("tool_calls", [])
                    for tc in tool_calls:
                        args = tc.get("arguments", {})
                        arg_str = str(args)
                        if "index.html" in arg_str:
                            print(f"\n--- MATCH IN STEP {step.get('step_index')} (type: {step.get('type')}) ---")
                            print(f"Tool: {tc.get('name')}")
                            print("Arguments:")
                            print(arg_str[:1000] + "...")
            except Exception as e:
                pass

if __name__ == "__main__":
    search_transcript()
