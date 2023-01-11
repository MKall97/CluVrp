def save_dict_to_json(d, filename):
    import json
    # Open the file for writing
    with open(filename, "w") as f:
        # Write the dictionary to the file as JSON
        json.dump(d, f)