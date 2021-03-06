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
bl_info = {'version'     : (1, 0, 0),
           'blender'     : (2, 70, 0),
           'name'        : 'Save back up files into subfolder',
           'author'      : 'Peter Varo',
           'description' : ('Cleans up CWD; Places back ups to subfolder; '
                            'Keeps subfolder organised.'),
           'category'    : 'System',
           'location'    : ("Go to 'File > User Preferences > File > Save "
                            "Versions' to set the number of back ups.")}

#------------------------------------------------------------------------------#
# Import Python modules
from errno import EEXIST
from os import ( makedirs as os_makedirs,
                 listdir as os_listdir,
                 remove as os_remove )
from os.path import ( dirname as os_path_dirname,
                      join as os_path_join,
                      isfile as os_path_isfile )
from traceback import extract_stack as traceback_extract_stack
from re import findall as re_findall
from shutil import move as shutil_move

# Import Blender modules
import bpy


#------------------------------------------------------------------------------#
# Module level constants
BACKUP_FOLDER_NAME = '__blendercache__'
PRINT_INFO = True
INFO_TEXT = 'Backup file(s) moved\n\tfrom:\n\t\t{!r}\n\tto\n\t\t{!r}'


#------------------------------------------------------------------------------#
def increase_index_and_move(src_folder, dst_folder, file, extension,
                            src_index, dst_index, max_index):
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
                                    dst_index=dst_index + 1,
                                    max_index=max_index)
        cleanup = ''
    # If destination file's index is equal or
    # greater than the maximum number of backups allowed
    else:
        src = path(src_folder, max_index - 1)
        dst = path(dst_folder, max_index)
        cleanup = path(src_folder, src_index)
    # Move source file to destination
    try:
        shutil_move(src, dst)
        return cleanup
    # If source does not found
    except FileNotFoundError:
        return ''


#------------------------------------------------------------------------------#
@bpy.app.handlers.persistent
def move_files_to_folder(*args, **kwargs):
    # Maximum backup allowed by user
    BACKUP_COUNT = bpy.context.user_preferences.filepaths.save_version
    # If saving backups option is 'ON'
    if BACKUP_COUNT:
        # Function level constants
        PATH = bpy.data.filepath                         # Full path
        FILE = bpy.path.display_name_from_filepath(PATH) # File name
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

        # Get all files in current directory, move them to the
        # backup folder, if they are backup files and maintain
        # the backup folder's instances
        for filename in reversed(sorted(os_listdir(CWD))):
            # If file is a backup file
            try:
                index = int(re_findall(REXT, filename)[-1])
                # If file's index is greater than the
                # current number of backups allowed the full path
                # of the file will be returned and will be deleted
                # else os.remove will raise FileNotFoundError
                os_remove(increase_index_and_move(src_folder=CWD,
                                                  dst_folder=CBD,
                                                  file=FILE,
                                                  extension=EXT,
                                                  src_index=index,
                                                  dst_index=index,
                                                  max_index=BACKUP_COUNT))
            # If file is not a backup file
            except (IndexError, FileNotFoundError):
                pass

        # If everything went fine, print out information
        if PRINT_INFO:
            print(INFO_TEXT.format(CWD, CBD))


#------------------------------------------------------------------------------#
def register():
    bpy.app.handlers.save_post.append(move_files_to_folder)

def unregister():
    bpy.app.handlers.save_post.remove(move_files_to_folder)

#------------------------------------------------------------------------------#
if __name__ == '__main__':
    register()
