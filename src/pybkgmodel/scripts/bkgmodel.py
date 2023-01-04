#!/usr/bin/env python3
import yaml
import argparse

# import regions

from pybkgmodel.message import message
from pybkgmodel.processing import RunwiseWobbleMap, StackedWobbleMap, RunwiseExclusionMap, StackedExclusionMap


def main():
    arg_parser = argparse.ArgumentParser(
        description="""
        IACT background generation tool
        """
    )

    arg_parser.add_argument(
        "--config", 
        default="config.yaml",
        help='Configuration file to steer the code execution.'
    )
    parsed_args = arg_parser.parse_args()

    config = yaml.load(open(parsed_args.config, "r"), Loader=yaml.SafeLoader)
    
    supported_modes = (
        'runwise_exclusion',
        'runwise_wobble',
        'stacked_exclusion',
        'stacked_wobble',
    )
    
    if config['mode'] not in supported_modes:
        raise ValueError(f"Unsupported mode '{config['mode']}', valid choices are '{supported_modes}'")

    message(f'Generating background maps')
    if config['mode'] == 'runwise_wobble':
        process_module = RunwiseWobbleMap.from_config_file(config)
    elif config['mode'] == 'stacked_wobble':
        process_module = StackedWobbleMap.from_config_file(config)
    elif config['mode'] == 'runwise_exclusion':
        process_module = RunwiseExclusionMap.from_config_file(config)
    elif config['mode'] == 'stacked_exclusion':
        process_module = StackedExclusionMap.from_config_file(config)
    else:
        ValueError(f"Unsupported mode '{config['mode']}'. This should have been caught earlier.")

    process_module.get_maps()

if __name__ == "__main__":
    main()
