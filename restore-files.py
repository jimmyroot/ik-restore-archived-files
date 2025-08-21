from locale import normalize
import os
import shutil
import argparse
import logging
from datetime import datetime
from tqdm import tqdm

def setup_logger(enable_logging, dry_run):
    if enable_logging:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"restore_log_{timestamp}.log"
        log_path = os.path.join(os.getcwd(), log_filename)
        
        logging.basicConfig(
            filename=log_path,
            filemode="w",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
        )

        mode = "DRY RUN" if dry_run else "ACTUAL RESTORE"
        logging.info(f"=== Script starting up... ===")
        logging.info(f"=== Mode: {mode} ===")

        return log_path
    else:
        logging.basicConfig(
            level=logging.CRITICAL,
        )
        return None

def log_and_print(message, level="info"):
    print(message)
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)

def construct_and_validate_paths(target_dir, archive_root):

    if not os.path.isdir(target_dir):
        raise ValueError(f"Target directory does not exist: {target_dir}")
    else: 
        # Construct the paths
        normalized_path = os.path.normpath(target_dir)
        split_path = normalized_path.split(os.path.sep)

        if "Shared" in split_path:
            index = split_path.index("Shared")    
            path_without_root = os.path.join(*split_path[index:])
        else:
            raise ValueError(f"Target directory must contain 'Shared' in the path (this script only works with Egnyte's 'Shared' directory): {target_dir}")
        
        full_archive_path = os.path.join(archive_root, path_without_root)
        
        if not os.path.isdir(full_archive_path):
            raise ValueError(f"Archive directory does not exist: {full_archive_path}")
        else:
            log_and_print(f"=== Target path is: {target_dir} ===")
            log_and_print(f"=== Archive path is: {full_archive_path} ===")
    
    return full_archive_path

def collect_txt_placeholders(path_to_target):
    placeholder_txt_files = []
    for dirpath, _, filenames in os.walk(path_to_target):
        for filename in filenames:
            if not filename.endswith(".txt"):
                continue
            
            placeholder_file_path = os.path.join(dirpath, filename)
            try:
                with open(placeholder_file_path, "r") as f:
                    first_line = f.readline().strip()
                    if "automatic archiving policy" not in first_line.lower():
                        log_and_print(f"IGNORED: {placeholder_file_path} - not an automatic archiving policy file")
                        continue
                    else:
                        placeholder_txt_files.append((dirpath, filename))

            except Exception as e:
                log_and_print(f"Error reading placeholder file {placeholder_file_path}: {e}", level="error")
                continue

    return placeholder_txt_files

def process_placeholder(dirpath, placeholder_filename, path_to_target, path_to_archive, dry_run):
    # Get the original filename, path, archived file name, placeholder, blah blah blah
    original_filename = placeholder_filename[:-4]
    relative_path = os.path.relpath(dirpath, path_to_target)
    archived_file = os.path.join(path_to_archive, relative_path, original_filename)
    target_file = os.path.join(dirpath, original_filename)
    placeholder_file = os.path.join(dirpath, placeholder_filename)

    # Check status of files and log the results
    if not os.path.isfile(archived_file):
        log_and_print(f"MISSING: {archived_file}")
        return "missing"
    
    if os.path.isfile(target_file):
        log_and_print(f"SKIPPED: {target_file}, because it already exists")
        return "skipped"
    
    # If dry run, log the results and return
    if dry_run:
        log_and_print(f"[DRY RUN] Would restore: {target_file}")
        log_and_print(f"[DRY RUN] Would delete placeholder: {placeholder_file}")
        return "restored"
    else:
        # OK now do the real work
        try:
            os.makedirs(dirpath, exist_ok=True)
            shutil.copy(archived_file, target_file)
            os.remove(placeholder_file)
            log_and_print(f"\nRESTORED: {target_file}")
            return "restored"
        except Exception as e:
            log_and_print(f"Error during restore of {target_file}: {e}", level="error")
            return "error"

# Main function to run the restore loop
def restore_archived_files(target_dir, archive_root, dry_run=True):
    path_to_target = target_dir
    path_to_archive= construct_and_validate_paths(target_dir, archive_root)
    placeholders = collect_txt_placeholders(path_to_target)

    restored = 0
    skipped = 0
    missing = 0
    errors = 0

    for dirpath, filename in tqdm(placeholders, desc="Restoring files", unit="file"):
        result = process_placeholder(dirpath, filename, path_to_target, path_to_archive, dry_run)

        match result:
            case "restored":
                restored += 1
            case "skipped":
                skipped += 1
            case "missing":
                missing += 1
            case "error":
                errors += 1
            case _:
                raise ValueError(f"Unknown result: {result}")
        
    return restored, skipped, missing, errors

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Restore files from an archive directory to the original location")
    parser.add_argument("--target-dir", "-t", required=True, help="Path to the target directory containing the .txt placeholders")
    parser.add_argument("--archive-root", "-a", required=True, help="Drive letter or mount point of the archive root directory")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Simulate a restoration without actually moving files")
    parser.add_argument("--log", "-l", action="store_true", help="Enable logging")

    args = parser.parse_args()

    try:
        mode = "DRY RUN" if args.dry_run else "RESTORE"
        print(f"=== Script starting up ===\n=== We are in {mode} mode ===\n=== The time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

        log_path = setup_logger(enable_logging=args.log, dry_run=args.dry_run)
        restored, skipped, missing, errors = restore_archived_files(
            args.target_dir, args.archive_root, dry_run=args.dry_run
        )
    
        summary = (
            f"\n=== Restore attempt finished ===\n"
            f"Restored: {restored} | Skipped: {skipped} | Missing: {missing} | Errors: {errors}\n"
        )

        log_and_print(summary)

        if log_path:
            print(f"Log file created: {log_path}")
            print(f"=== Script finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            print("=== Exiting... ===")
            print("=== Goodbye! ===")
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        log_and_print(f"FATAL ERROR: {e}", level="error")

if __name__ == "__main__":
    main()