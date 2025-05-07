import argparse
import os
import re

def create_chrom_state_trackdb(file_list_path, base_url, parent_track_id):
    """
    Generates UCSC trackDb entries for chromatin state bigBed files,
    grouped under a parent composite track.

    Args:
        file_list_path (str): Path to a file containing a list of bigBed file paths.
        base_url (str): The base URL where the bigBed files are hosted.
        parent_track_id (str): The track ID for the parent composite track.
    """
    print(f"# --- Chromatin State Tracks ---")

    # --- Print Parent Track Definition ---
    print(f"track {parent_track_id}")
    print(f"compositeTrack on")
    print(f"shortLabel IDC Chromatin States")
    print(f"longLabel P. falciparum chromatin states during the IDC")
    # Note: 'type bigBed' is specified here as requested, though sometimes omitted for composites.
    # Subtrack types define the actual data format.
    print(f"type bigBed")
    print(f"visibility dense") # Parent container visibility
    # Add other parent track settings if needed (e.g., group, html)
    print("")

    # --- Process Subtracks ---
    try:
        priority_counter = 1 # Start priority for subtracks

        with open(file_list_path, 'r') as f_list:
            for line in f_list:
                full_path = line.strip()
                if not full_path:
                    continue # Skip empty lines

                # 1. Extract the filename
                filename = os.path.basename(full_path) # e.g., "10hpi_chrom-states.bb"

                # 2. Extract the track identifier (e.g., "10hpi")
                match = re.match(r"^(\d+hpi)", filename, re.IGNORECASE)

                if not match:
                    print(f"# Warning: Could not extract identifier from filename: {filename}. Skipping.")
                    continue

                subtrack_id = match.group(1) # e.g., "10hpi"

                # Construct the bigDataUrl
                big_data_url = f"{base_url}/{filename}"

                # --- Generate Subtrack Entry ---
                # Use a unique identifier for the track line itself within the hub
                # often combining parent and subtrack IDs.
                track_line_id = f"{parent_track_id}_{subtrack_id}"
                print(f"track {track_line_id}")
                # Add the parent line to link it
                print(f"parent {parent_track_id} on") # Link to parent, default visible
                print(f"type bigBed 9 +")
                print(f"shortLabel {subtrack_id} States") # Label shown within the composite
                print(f"longLabel Chromatin States for {subtrack_id}")
                print(f"visibility dense") # Visibility within the composite
                print(f"itemRgb on")
                print(f"bigDataUrl {big_data_url}")
                print(f"priority {priority_counter}")
                print("") # Add a blank line between entries

                priority_counter += 1 # Increment priority for next subtrack

    except FileNotFoundError:
        print(f"# Error: Input file not found at {file_list_path}")
    except Exception as e:
        print(f"# An error occurred: {e}")



# --- Function for Histone Mark / Signal Tracks (bigWig) ---
def create_signal_trackdb(file_list_path, base_url, parent_track_id):
    """
    Generates UCSC trackDb entries for signal tracks (like histone marks, ATAC)
    in bigWig format, grouped under a parent composite track with subgroups.

    Subgroups:
        1. Timepoint (e.g., 10hpi, 20hpi)
        2. Mark_Source (e.g., H3K4me3_Stunnenberg, ATAC_Bartfai)
    """
    print(f"# --- Histone Mark / Signal Tracks (with Subgroups) ---")

    subtrack_data = []
    timepoints = set()
    mark_sources = set() # Store combined "Mark_Source" strings

    # --- First Pass: Read files, parse info, collect unique subgroup values ---
    try:
        with open(file_list_path, 'r') as f_list:
            for line in f_list:
                full_path = line.strip()
                if not full_path: continue

                filename = os.path.basename(full_path)
                # Regex to parse: MARK_TIMEPOINT_SOURCE_ID.bw
                match = re.match(r"^(.*?)_(\d+hpi)_(.*?)_(.*?)\.bw$", filename, re.IGNORECASE)

                if not match:
                    print(f"# Warning: Could not parse signal filename: {filename}. Skipping.")
                    continue

                mark = match.group(1).replace('-', '.') # Standardize H2A-Z to H2A.Z
                timepoint = match.group(2)
                source = match.group(3)
                source_id = match.group(4)
                mark_source_key = f"{mark}_{source}" # Combine mark and source

                # Add unique values to sets
                timepoints.add(timepoint)
                mark_sources.add(mark_source_key)

                # Store data for the second pass
                subtrack_data.append({
                    'filename': filename,
                    'mark': mark,
                    'timepoint': timepoint,
                    'source': source,
                    'source_id': source_id,
                    'mark_source_key': mark_source_key
                })

    except FileNotFoundError:
        print(f"# Error: Signal track input file not found at {file_list_path}")
        return # Stop processing if the file isn't found
    except Exception as e:
        print(f"# An error occurred during the first pass of signal tracks: {e}")
        return # Stop processing on error

    if not subtrack_data:
        print(f"# No valid signal track data found in {file_list_path}")
        return

    # --- Generate Tags for Subgroups ---
    # Sort for consistent order
    sorted_timepoints = sorted(list(timepoints), key=lambda x: int(re.search(r'\d+', x).group()))
    sorted_mark_sources = sorted(list(mark_sources))

    # Create clean tags (alphanumeric)
    timepoint_tags = {tp: f"t{tp.replace('hpi', '')}" for tp in sorted_timepoints}
    mark_source_tags = {ms: f"ms{re.sub(r'[^a-zA-Z0-9]', '', ms)}" for ms in sorted_mark_sources}

    # --- Print Parent Track Definition with Subgroups ---
    print(f"track {parent_track_id}")
    print(f"compositeTrack on")
    print(f"shortLabel Histone Marks")
    print(f"longLabel P. falciparum Histone Marks and Accessibility")
    print(f"type bigWig")
    print(f"visibility full")
    print(f"autoScale off")
    print(f"groupAutoScale on")
    print(f"group regulation")
    print(f"priority 20")
    print(f"dragAndDrop subTracks") # Enable drag-and-drop rearrangement
    print(f"noInherit on") # Subtrack settings (color, visibility) are specific

    # SubGroup Definitions
    sg1_items = " ".join([f"{tag}={val}" for val, tag in timepoint_tags.items()])
    print(f"subGroup1 timepoint Timepoint {sg1_items}")

    sg2_items = " ".join([f"{tag}={val}" for val, tag in mark_source_tags.items()]) # Use original key for display value
    print(f"subGroup2 markSource Mark_Source {sg2_items}")

    # Dimensions and Sorting
    print(f"dimensions dimX=timepoint dimY=markSource")
    print(f"sortOrder timepoint=+ markSource=+") # Sort by timepoint, then mark/source
    print("")

    # --- Second Pass: Print Subtrack Entries ---
    priority_counter = 21 # Reset priority counter for subtracks
    for data in subtrack_data:
        # Retrieve data from the stored dictionary
        filename = data['filename']
        mark = data['mark']
        timepoint = data['timepoint']
        source = data['source']
        source_id = data['source_id']
        mark_source_key = data['mark_source_key']

        # Get subgroup tags for this specific track
        tp_tag = timepoint_tags[timepoint]
        ms_tag = mark_source_tags[mark_source_key]

        # Define visibility and color (same logic as before)
        visibility = "hide"
        color = "128,128,128"
        if mark.upper() == "INPUT":
            color = "150,150,150"
        elif "ATAC" in mark.upper():
            visibility = "full"
            color = "153,50,204"
        elif "H3K4me3" in mark or "H3K9ac" in mark or "H3K27ac" in mark or "H3K18ac" in mark:
             color = "0,128,0"
        elif "H3K9me3" in mark or "H3K27me3" in mark:
             color = "255,0,0"
        elif "H2A.Z" in mark:
             color = "0,0,255"

        # Create labels and IDs
        short_label = f"{mark} {timepoint} ({source})" # Keep short label concise
        long_label = f"{mark} signal at {timepoint} from {source} ({source_id})"
        # Use a simpler track suffix for the track line ID if needed
        track_suffix = f"{mark.replace('.', 'z')}_{timepoint}_{source}"
        track_line_id = f"{parent_track_id}_{track_suffix}"
        track_line_id = re.sub(r'[^\w-]', '_', track_line_id)[:50] # Clean and shorten ID

        big_data_url = f"{base_url}/{filename}"

        # Print Subtrack Entry
        print(f"    track {track_line_id}")
        print(f"    parent {parent_track_id} on")
        # Add the subGroups line
        print(f"    subGroups timepoint={tp_tag} markSource={ms_tag}")
        print(f"    type bigWig")
        print(f"    shortLabel {short_label}") # Label shown in menus/tooltips
        print(f"    longLabel {long_label}")
        print(f"    visibility {visibility}")
        print(f"    color {color}")
        print(f"    autoScale off")
        print(f"    bigDataUrl {big_data_url}")
        print(f"    priority {priority_counter}")
        print("")
        priority_counter += 1


# --- Function for Transcription Factor (TF) Tracks (with combined Factor_Source subgroup) ---
def create_tf_trackdb(file_list_path, base_url, parent_track_id):
    """
    Generates UCSC trackDb entries for TF ChIP-seq tracks (signal and peaks)
    in bigWig/bigBed format, grouped under a parent composite track with subgroups.

    Subgroups:
        1. View (Signal/Peaks)
        2. Factor_Source (TF Name (Source))
        3. Timepoint
    """
    print(f"# --- Transcription Factor (TF) Tracks (with combined Factor_Source subgroup) ---")

    subtrack_data = []
    # Store tuples of (tf_name, source_name)
    factor_sources = set()
    timepoints = set()
    # View types are predefined
    view_map = {"Signal": "sig", "Peaks": "pk"} # Short tags for view

    # --- First Pass: Read files, parse info, collect unique subgroup values ---
    try:
        with open(file_list_path, 'r') as f_list:
            for line in f_list:
                full_path = line.strip()
                if not full_path: continue

                filename = os.path.basename(full_path)
                view_type = ""
                file_type_for_regex = ""

                if filename.endswith(".narrowPeak.bb"):
                    view_type = "Peaks"
                    file_type_for_regex = r"\.narrowPeak\.bb"
                elif filename.endswith(".bw"):
                    view_type = "Signal"
                    file_type_for_regex = r"\.bw"
                else:
                    print(f"# Warning: Unknown file type for TF track: {filename}. Skipping.")
                    continue

                regex_pattern = r"^(.*?)_(\d+hpi)_([a-zA-Z0-9]+)_(.*?)" + file_type_for_regex + "$"
                match = re.match(regex_pattern, filename, re.IGNORECASE)

                if not match:
                    regex_pattern_simple = r"^(.*?)_(\d+hpi)_([a-zA-Z0-9]+)_(.*)" + file_type_for_regex + "$" # Simpler, for cases like 'unpublished'
                    match = re.match(regex_pattern_simple, filename, re.IGNORECASE)
                    if not match:
                        print(f"# Warning: Could not parse TF filename: {filename} with pattern. Skipping.")
                        continue
                
                tf_name = match.group(1)
                timepoint = match.group(2)
                source_name = match.group(3)
                source_id = match.group(4)

                # Create a key for the combined factor and source
                factor_source_key = (tf_name, source_name)

                # Add unique values to sets
                factor_sources.add(factor_source_key)
                timepoints.add(timepoint)

                # Store data for the second pass
                subtrack_data.append({
                    'filename': filename,
                    'tf_name': tf_name,
                    'timepoint': timepoint,
                    'source_name': source_name,
                    'source_id': source_id,
                    'view_type': view_type,
                    'factor_source_key': factor_source_key # Store the combined key
                })

    except FileNotFoundError:
        print(f"# Error: TF track input file not found at {file_list_path}")
        return
    except Exception as e:
        print(f"# An error occurred during the first pass of TF tracks: {e}")
        return

    if not subtrack_data:
        print(f"# No valid TF track data found in {file_list_path}")
        return

    # --- Generate Tags for Subgroups ---
    # Sort for consistent order
    # Sort factor_sources by TF name, then by source name
    sorted_factor_sources = sorted(list(factor_sources), key=lambda x: (x[0].lower(), x[1].lower()))
    sorted_timepoints = sorted(list(timepoints), key=lambda x: int(re.search(r'\d+', x).group()))

    # Create clean tags (alphanumeric, short)
    # Tag for Factor_Source combines cleaned TF and Source names
    factor_source_tags = {
        fs_key: f"fs{re.sub(r'[^a-zA-Z0-9]', '', fs_key[0])[:10]}{re.sub(r'[^a-zA-Z0-9]', '', fs_key[1])[:5]}"
        for fs_key in sorted_factor_sources
    }
    timepoint_tags = {tp: f"t{tp.replace('hpi', '')}" for tp in sorted_timepoints}


    # --- Print Parent Track Definition with Subgroups ---
    print(f"track {parent_track_id}")
    print(f"compositeTrack on")
    print(f"shortLabel TFs")
    print(f"longLabel P. falciparum Transcription Factor ChIP-seq")
    print(f"visibility dense")
    print(f"group regulation")
    print(f"priority 30")
    print(f"dragAndDrop subTracks")
    print(f"noInherit on")

    # SubGroup Definitions
    print(f"subGroup1 view Views Signal={view_map['Signal']} Peaks={view_map['Peaks']}")
    sg2_items = " ".join([f"{tag}={val}" for val, tag in timepoint_tags.items()])
    print(f"subGroup2 timepoint Timepoint {sg2_items}")
    # For subGroup3, display value is "TF_Source"
    sg3_items = " ".join([f"{tag}={key[0]}_{key[1]}" for key, tag in factor_source_tags.items()])
    print(f"subGroup3 factorSource Factor_Source {sg3_items}")
    

    # Dimensions and Sorting
    print(f"dimensions dimX=factorSource dimY=timepoint dimA=view") # Adjusted dimensions
    print(f"sortOrder view=+ factorSource=+ timepoint=+") # Adjusted sort order
    print(f"visibilityViewDefaults {view_map['Signal']}=full {view_map['Peaks']}=hide")
    print("")


    # --- Second Pass: Print Subtrack Entries ---
    priority_counter = 1
    for data in subtrack_data:
        filename = data['filename']
        tf_name = data['tf_name']
        timepoint = data['timepoint']
        source_name = data['source_name']
        source_id = data['source_id']
        view_type = data['view_type']
        factor_source_key = data['factor_source_key'] # Retrieve the key

        # Get subgroup tags
        view_tag = view_map[view_type]
        fs_tag = factor_source_tags[factor_source_key] # Use the combined key to get the tag
        tp_tag = timepoint_tags[timepoint]

        clean_tf = re.sub(r'[^a-zA-Z0-9_]', '', tf_name)
        clean_src = re.sub(r'[^a-zA-Z0-9_]', '', source_name)
        track_line_id = f"{parent_track_id}_{clean_tf}_{clean_src}_{timepoint}_{view_tag}"
        track_line_id = track_line_id[:60]

        big_data_url = f"{base_url}/{filename}"
        
        short_label_view_suffix = "Sig" if view_type == "Signal" else "Pks"
        short_label = f"{tf_name} ({source_name}) {timepoint} {short_label_view_suffix}"
        long_label = f"TF {tf_name} ({source_name}) at {timepoint} from {source_id} - {view_type}"

        print(f"    track {track_line_id}")
        print(f"    parent {parent_track_id} on")
        # Adjusted subGroups attribute
        print(f"    subGroups view={view_tag} factorSource={fs_tag} timepoint={tp_tag}")
        
        if view_type == "Signal":
            print(f"    type bigWig")
            print(f"    shortLabel {short_label}")
            print(f"    longLabel {long_label}")
            print(f"    color 0,0,170")
            print(f"    autoScale off")
            print(f"    groupAutoScale on")
        elif view_type == "Peaks":
            print(f"    type bigBed 6 +")
            print(f"    shortLabel {short_label}")
            print(f"    longLabel {long_label}")
            print(f"    color 0,0,0")
            # print(f"    itemRgb on") # Uncomment if bigBed files have per-item RGB

        print(f"    bigDataUrl {big_data_url}")
        print(f"    priority {priority_counter:}")
        print("")
        priority_counter += 1


# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate UCSC trackDb entries for Chromatin States (bigBed) and Histone Marks/Signal (bigWig)."
    )
    parser.add_argument(
        "chrom_state_list",
        help="Path to the file containing a list of chromatin state bigBed files (e.g., data/XXhpi_chrom-states.bb)."
    )
    parser.add_argument(
        "signal_list",
        help="Path to the file containing a list of histone mark signal bigWig files (e.g., data/MARK_TIMEPOINT_SOURCE_ID.bw)."
    )
    parser.add_argument(
        "tf_list",
        help="Path to the file containing a list of TF signal bigWig files & narrowPeak bigBed files (e.g., data/MARK_TIMEPOINT_SOURCE_ID.bw)."
    )
    # Optional: Add argument for base URL if needed
    # parser.add_argument("--base_url", default="DEFAULT_URL", help="Base URL for track data.")

    args = parser.parse_args()

    BASE_URL = "http://e1-lugh2.science.psu.edu/data/ucsc_tracks/mahony/plasmodium-chrom-states/data"

    # Define Parent Track IDs
    CHROM_STATE_PARENT_ID = "PfalChromStates" 
    HISTONE_PARENT_ID = "PfalHistoneMarks" 
    TF_PARENT_ID = "PfalTFs"   

    # Call function for Chromatin States
    create_chrom_state_trackdb(args.chrom_state_list, BASE_URL, CHROM_STATE_PARENT_ID)

    # Call function for Histone Marks / Signal Tracks
    create_signal_trackdb(args.signal_list, BASE_URL, HISTONE_PARENT_ID)

    # Call function for TFs / Signal Tracks & Peaks
    #create_tf_trackdb(args.tf_list, BASE_URL, TF_PARENT_ID)

