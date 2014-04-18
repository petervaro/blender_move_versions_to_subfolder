################################################################################
##                                                                            ##
##                DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE                 ##
##                        Version 2, December 2004                            ##
##                                                                            ##
##      Copyright (C) 2014 Peter Varo <petervaro@sketchandprototype.com>      ##
##                                                                            ##
##     Everyone is permitted to copy and distribute verbatim or modified      ##
##     copies of this license document, and changing it is allowed as long    ##
##     as the name is changed.                                                ##
##                                                                            ##
##                DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE                 ##
##      TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION       ##
##                                                                            ##
##      0. You just DO WHAT THE FUCK YOU WANT TO.                             ##
##                                                                            ##
################################################################################

# Blender Informations
bl_info = {'version'     : (0, 9, 2),
           'blender'     : (2, 70, 0),
           'name'        : "Save backupfiles into '__blendercache__' folder",
           'author'      : 'Peter Varo',
           'description' : "Save backupfiles into '__blendercache__' folder" ,
           'category'    : 'System',
           'location'    : ("Go to 'File > User Preferences > File > Save "
                            "Versions' to change the number of backups this "
                            "script will save.")}

#------------------------------------------------------------------------------#
# Import Python modules
from errno import EEXIST
from os import ( makedirs as os_makedirs,
                 listdir as os_listdir)
from os.path import ( dirname as os_path_dirname,
                      join as os_path_join,
                      isfile as os_path_isfile )
from traceback import extract_stack as traceback_extract_stack
from re import findall as re_findall
from shutil import move as shutil_move

# Import Blender modules
from bpy import (data as bpy_data,
                 context as bpy_context)
from bpy.app.handlers import ( persistent as bpy_app_handlers_persistent,
                               save_post as bpy_app_handlers_save_post )
from bpy.path import display_name_from_filepath as bpy_path_display_name_from_filepath


#------------------------------------------------------------------------------#
# Module level constants
BACKUP_FOLDER_NAME = '__blendercache__'
BACKUP_COUNT = bpy_context.user_preferences.filepaths.save_version
PRINT_INFO = True
INFO_TEXT = 'Backup file(s) moved\n\tfrom:\n\t\t{!r}\n\tto\n\t\t{!r}'


#------------------------------------------------------------------------------#
def increase_index_and_move(src_folder, dst_folder, file, extension,
                            src_index, dst_index, max_index=BACKUP_COUNT):
    # Helper function to format the full source and destination path
    path = lambda f, i: os_path_join(f, extension.format(file, i))
    # If destination file's index is lesser than
    # the maximum number of backups allowed
    if src_index <= max_index:
        src = path(src_folder, src_index)
        dst = path(dst_folder, dst_index)
        # If the destination file exists
        if os_path_isfile(dst):
            # Call this function recursivly
            increase_index_and_move(src_folder=dst_folder,
                                    dst_folder=dst_folder,
                                    file=file,
                                    extension=extension,
                                    src_index=dst_index,
                                    dst_index=dst_index + 1)
    # If destination file's index is equal or
    # greater than the maximum number of backups allowed
    else:
        src = path(src_folder, max_index - 1)
        dst = path(dst_folder, max_index)
    # Move source file to destination
    try:
        shutil_move(src, dst)
    # If source does not found
    except FileNotFoundError:
        return


#------------------------------------------------------------------------------#
@bpy_app_handlers_persistent
def move_files_to_folder(*args, **kwargs):
    # If saving backups option is 'ON'
    if BACKUP_COUNT:
        # Function level constants
        PATH = bpy_data.filepath                         # Full path
        FILE = bpy_path_display_name_from_filepath(PATH) # File name
        CWD  = os_path_dirname(PATH)                     # Current Working Directory
        CBD  = os_path_join(CWD, BACKUP_FOLDER_NAME)     # Current Backup Directory
        REXT = r'{}\.blend(\d+)$'.format(FILE)           # Regex to catch backups
        EXT  = '{}.blend{}'                              # Extension placeholder
        OLD  = EXT.format(FILE, BACKUP_COUNT)            # Oldest backup name

        # Create backup directory if not exists
        try:
            os_makedirs(CBD)
        except OSError as e:
            if e.errno != EEXIST:
                # If other error appears then "dir already exists" reraise
                # the caught error again and print out the traceback
                raise OSError('\n'.join(traceback_extract_stack())) from None

        # TODO: Cleanup: delete files if their index is greater than max_index!

        # Get all files in current directory, move them to the
        # backup folder, if they are backup files and maintain
        # the backup folder's instances
        for filename in reversed(sorted(os_listdir(CWD))):
            # If file is a backup file
            try:
                index = int(re_findall(REXT, filename)[-1])
                increase_index_and_move(src_folder=CWD,
                                        dst_folder=CBD,
                                        file=FILE,
                                        extension=EXT,
                                        src_index=index,
                                        dst_index=index)
            # If file is not a backup file
            except IndexError:
                pass

        # If everything went fine, print out information
        if PRINT_INFO:
            print(INFO_TEXT.format(CWD, CBD))


#------------------------------------------------------------------------------#
def register():
    bpy_app_handlers_save_post.append(move_files_to_folder)

def unregister():
    bpy_app_handlers_save_post.remove(move_files_to_folder)

#------------------------------------------------------------------------------#
if __name__ == '__main__':
    register()
