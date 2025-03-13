import yaml

def merge_playlists(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)

    output_filename = config['output']['filename']
    add_newlines = config['output']['add_newlines']
    input_files = config['input_files']
    success_message = config['logging']['success_message']

    with open(output_filename, 'w') as outfile:
        for fname in input_files:
            with open(fname) as infile:
                outfile.write(infile.read())
                if add_newlines:
                    outfile.write('\n')

    if config['logging']['enabled']:
        print(success_message.format(output_filename=output_filename))

if __name__ == "__main__":
    merge_playlists('python-merges.yml')