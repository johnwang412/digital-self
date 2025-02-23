"""
Operates on output files of directory parser that parses raw html google voice
dumps. Takes the output files and formats them according to Apple MLX training
format.


"""

import os
import json
from datetime import datetime, timedelta

# Configuration
INPUT_DIR = "input_jsons"  # Directory containing JSON files
OUTPUT_DIR = "output_jsons"  # Directory to save processed files
TIME_THRESHOLD = timedelta(hours=2)  # Messages within 12 hours are grouped

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_json_file(input_filepath, output_filepath):
    # Load JSON file
    with open(input_filepath, "r") as f:
        messages = json.load(f)

    # Convert timestamps to datetime objects
    for msg in messages:
        msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])

    # Sort messages by timestamp
    messages.sort(key=lambda x: x["timestamp"])

    # Group messages
    grouped_messages = []
    current_group = []

    for msg in messages:
        if not current_group:
            if msg["role"] == "user":
                current_group.append(msg)
            else:
                continue
        else:
            last_msg_time = current_group[-1]["timestamp"]
            last_role = current_group[-1]["role"]
            curr_role = msg["role"]
            """
            Append if role matches and time is within threshold
            Otherwise, break: only add to grouped messages if current group
              meets standard
            """
            if (curr_role == 'user' and last_role == 'assistant') or \
                    msg["timestamp"] - last_msg_time > TIME_THRESHOLD:
                # Done with current group, append if relevant
                if last_role == 'assistant':
                    # This means we've picked up a set of user msgs and then
                    # a set of assistant msgs
                    grouped_messages.append(current_group)
                if curr_role == 'user':
                    current_group = [msg]
                else:
                    current_group = []
            else:
                # Keep adding to current group
                current_group.append(msg)

    if current_group:
        grouped_messages.append(current_group)

    # Merge consecutive messages from the same user within each group
    transformed_groups = []

    for group in grouped_messages:
        merged_group = []
        current_message = group[0]  # Start with the first message

        for msg in group[1:]:
            if msg["role"] == current_message["role"]:
                # Merge content
                current_message["content"] += ". " + msg["content"]
            else:
                # Append the last merged message and start a new one
                merged_group.append({
                    "role": current_message["role"],
                    "content": current_message["content"],
                    # "timestamp": current_message["timestamp"].isoformat()
                })
                current_message = msg

        # Append the last message in the group
        merged_group.append({
            "role": current_message["role"],
            "content": current_message["content"],
            # "timestamp": current_message["timestamp"].isoformat()
        })

        transformed_groups.append(merged_group)

    # Save the transformed JSON file
    with open(output_filepath, "w") as f:
        for grp in transformed_groups:
            f.write(json.dumps({"messages": grp}) + '\n')

# Process all JSON files in the input directory
for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".json"):
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, "new-" + filename)
        process_json_file(input_path, output_path)
        print(f"Processed: {filename} → {output_path}")

print("All files processed successfully!")

