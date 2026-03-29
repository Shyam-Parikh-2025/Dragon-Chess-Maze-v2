import os

def combine_source_code(output_filename="Pair27_Full_Source_Code.txt"):
    # The folder where your actual game code lives
    source_folder = "."
    ignore_files = [output_filename, "file_combiner.py", ".DS_Store", 
                    "rook_vbo.py", "queen_vbo.py", "king_vbo.py"]
    found_any = False
    
    # Check if the folder even exists first
    if not os.path.exists(source_folder):
        print(f"❌ Error: The folder '{source_folder}' was not found!")
        return

    with open(output_filename, "w", encoding="utf-8") as outfile:
        outfile.write("="*60 + "\n")
        outfile.write("PROJECT: DRAGON CHESS MAZE - FULL SOURCE CODE\n")
        outfile.write("TEAM: SHYAM PARIKH & SAMUEL BONCIK [cite: 40]\n")
        outfile.write("="*60 + "\n\n")

        # Now we list files inside the 'game' folder specifically
        for filename in sorted(os.listdir(source_folder)):
            if filename.endswith(".py") and filename not in ignore_files:
                file_path = os.path.join(source_folder, filename)
                print(f"Adding: {file_path}...") 
                found_any = True
                
                outfile.write(f"\n{'='*60}\nSOURCE FILE: {filename}\n{'='*60}\n\n")
                
                with open(file_path, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
                    outfile.write("\n")

    if found_any:
        print(f"\n✅ Success! Code from '{source_folder}' combined into {output_filename}")
    else:
        print(f"\n❌ Error: No .py files were found inside the '{source_folder}' folder!")

if __name__ == "__main__":
    combine_source_code()