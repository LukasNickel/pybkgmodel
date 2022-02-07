#!/usr/bin/env python3
import yaml
import argparse

# import regions

from aux.message import message
from aux.data import RunSummary
from aux.processing import process_runwise_wobble_map


if __name__ == "__main__":
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
        # 'wobble',
        'runwise_wobble'
    )

    if config['mode'] not in supported_modes:
        raise RuntimeError(f"Unsupported mode '{config['mode']}', valid choices are '{supported_modes}'")

    message(f'Geneting background maps')
    if config['mode'] == 'runwise_wobble':
        process_runwise_wobble_map(config)
