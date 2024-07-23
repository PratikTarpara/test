import subprocess
import os

def convert_stl_to_gcode(stl_file_path, output_folder, layer_height):
    # Determine the OS-specific path to PrusaSlicer executable
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.name == 'nt':  # Windows
        prusa_slicer_executable = os.path.join("C:\\Program Files\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe")
    elif os.name == "posix":  # Linux/Unix (Ubuntu)
        prusa_slicer_executable = os.path.join(script_dir, '../../../../slicer/prusa-slicer')
    else:
        raise OSError("Unsupported operating system.")

    # Ensure the path is normalized
    prusa_slicer_executable = os.path.normpath(prusa_slicer_executable)
    print(f"PrusaSlicer executable path: {prusa_slicer_executable}")

    # Check if PrusaSlicer executable exists
    if not os.path.isfile(prusa_slicer_executable):
        raise FileNotFoundError(f"PrusaSlicer executable not found at {prusa_slicer_executable}")

    # Check if the STL file exists
    if not os.path.isfile(stl_file_path):
        raise FileNotFoundError(f"STL file not found at {stl_file_path}")

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Generate the output G-code file path
    output_gcode_file = os.path.join(output_folder, "output.gcode")
    print(f"Output G-code file path: {output_gcode_file}")

    # Command to convert STL to G-code with specified layer height
    command = [
        prusa_slicer_executable,
        "--export-gcode",
        f"--output={output_gcode_file}",
        f"--layer-height={layer_height}",
        stl_file_path
    ]
    print(f"Command to be executed: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("STL to G-code conversion completed successfully.")
        print(f"Output: {result.stdout}")
        print(f"Error Output: {result.stderr}")
        return output_gcode_file
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        print(f"Output: {e.output}")
        print(f"Error Output: {e.stderr}")
        return None

def extract_gcode_info(gcode_file_path):
    material_type = None
    filament_used = None
    estimated_print_time = None

    with open(gcode_file_path, 'r') as file:
        for line in file:
            line = line.strip()

            if '; filament used [cm3]' in line:
                try:
                    filament_used = float(line.split('=')[1].strip())
                except (IndexError, ValueError):
                    pass

            if '; estimated printing time (normal mode)' in line:
                try:
                    estimated_print_time = line.split('=')[1].strip()
                except IndexError:
                    pass

            if '; filament_type' in line:
                try:
                    material_type = line.split('=')[1].strip()
                except IndexError:
                    pass

    return {
        'filament_used': filament_used,
        'estimated_print_time': estimated_print_time,
        'material_type': material_type
    }

# Paths and parameters
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Script directory: {script_dir}")

# Correct the path to the STL file
stl_file_path = os.path.normpath(os.path.join(script_dir, 'test.stl'))
output_folder = os.path.normpath(os.path.join(script_dir, 'output'))
manual_layer_height = 0.2

# Check if the STL file exists before proceeding
if not os.path.isfile(stl_file_path):
    print(f"STL file not found at {stl_file_path}. Please check the path.")
else:
    # Conversion and extraction
    output_gcode_file = convert_stl_to_gcode(stl_file_path, output_folder, manual_layer_height)
    if output_gcode_file:
        gcode_info = extract_gcode_info(output_gcode_file)
        print(gcode_info)
    else:
        print("Conversion failed.")
