import os

def create_district_report_dirs():
    '''
    Since empty folders are not captured in GitLab, the folder structure for sorting the result files
    should be created automatically, if the folders do not exist yet.
    '''
    # Create report data folders if they don't exist already
    root = 'district_reports'
    midFolders = ['life_cycle_inventory', 'life_cycle_impact']
    for midFolder in midFolders:
        # exist_ok = True: if directories already exist leave them unaltered
        os.makedirs(os.path.join(root, midFolder), exist_ok=True)
