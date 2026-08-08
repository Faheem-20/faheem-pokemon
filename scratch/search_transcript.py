import json
import re

LOG_PATH = r'C:\Users\simha\.gemini\antigravity\brain\25a83453-80fa-4f95-9063-1aa53533ed06\.system_generated\logs\transcript_full.jsonl'

print("Searching transcript_full.jsonl for write/replace calls on events.html...")
found_steps = []

with open(LOG_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            step = json.loads(line)
            tool_calls = step.get('tool_calls', [])
            for call in tool_calls:
                args = call.get('args', {})
                target = args.get('TargetFile', '')
                if 'events.html' in target:
                    found_steps.append((step.get('step_index'), call.get('name'), args))
        except Exception as e:
            pass

print(f"Found {len(found_steps)} operations on events.html.")
for step_idx, name, args in found_steps:
    print(f"\nStep {step_idx}: Tool '{name}'")
    if name == 'write_to_file':
        print(f"Write code length: {len(args.get('CodeContent', ''))}")
        out_path = f"scratch/events_step_{step_idx}.html"
        with open(out_path, 'w', encoding='utf-8') as out_f:
            out_f.write(args.get('CodeContent', ''))
        print(f"Saved content to {out_path}")
    elif name == 'replace_file_content':
        print(f"Replace instruction: {args.get('Instruction', '')}")
        print(f"Replacement content length: {len(args.get('ReplacementContent', ''))}")
