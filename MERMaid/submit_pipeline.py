import argparse
import subprocess
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Submit pipeline job")
    parser.add_argument("--VH-Input-Dir", type=str, required=True)
    parser.add_argument("--VH-Output-Dir", type=str, required=True)
    parser.add_argument("--DIS-Input-Dir", type=str, required=False)
    parser.add_argument("--DIS-Output-Dir", type=str, required=False)
    parser.add_argument("--DIS-Excel-Output-Name", type=str, required=False)       
    parser.add_argument("--CXMS-Excel-Output-Name", type=str, required=False)
   
    args = parser.parse_args()

    script = "./pipeline_sub.sh"
    script_args = [
	"--VH-Input-Dir", args.VH_Input_Dir,
	"--VH-Output-Dir", args.VH_Output_Dir,
        "--DIS-Input-Dir", args.DIS_Input_Dir,
        "--DIS-Output-Dir", args.DIS_Output_Dir,
        "--DIS-Excel-Output-Name", args.DIS_Excel_Output_Name,
        "--CXMS-Excel-Output-Name", args.CXMS_Excel_Output_Name,
	]

    command = [script] + script_args
	
    result = subprocess.run(command)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

