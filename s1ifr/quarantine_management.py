import datetime
import logging
import os
import shutil

from s1ifr.SAFEsortingfunctions import whichquarantinedir


def quarantine_ticket(safe_full_path: str, other_archive: str) -> None:
    """Moves a corrupted SAFE product to quarantine.

    This function handles a failed product by creating a "ticket" in the
    quarantine directory and then deleting the original SAFE file or directory.
    The ticket is a file named after the SAFE product, containing timestamps
    of each time it was quarantined.

    Args:
        safe_full_path: The full path to the corrupted .SAFE file or directory.
        other_archive: The name of the archive (e.g., 'datawork', 'scale')
            where the quarantine directory is located.
    """
    base_safe = os.path.basename(safe_full_path)
    path_ticket = os.path.join(
        whichquarantinedir(archive=other_archive), base_safe
    )

    # Use 'with open' for safer file handling. It ensures the file is
    # closed automatically, even if errors occur.
    mode = "a" if os.path.exists(path_ticket) else "w"
    with open(path_ticket, mode) as fid:
        fid.write(
            datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S") + "\n"
        )

    remove_safe_from_disk(safe_full_path)


def remove_safe_from_disk(safe_full_path: str) -> None:
    """Deletes a file or an entire directory tree from the disk.

    This function checks if the provided path is a file or a directory
    and uses the appropriate method to remove it.

    Args:
        safe_full_path: The full path to the file or directory to be removed.
    """
    if os.path.isfile(safe_full_path):
        os.remove(safe_full_path)
    elif os.path.isdir(safe_full_path):
        shutil.rmtree(safe_full_path)
    else:
        logging.warning(
            "Path %s is neither a file nor a directory. Cannot remove.",
            safe_full_path,
        )
        return
    logging.info("%s deleted", safe_full_path)


def test_quarantine_before_download(safe_full_path: str, archive: str) -> bool:
    """Checks if a SAFE product is blacklisted by examining its quarantine ticket.

    A product is considered blacklisted if its corresponding quarantine ticket
    exists and contains 10 or more entries, which indicates repeated
    processing failures.

    Args:
        safe_full_path: The path of the SAFE product to check.
        archive: The name of the archive where the quarantine directory resides.

    Returns:
        True if the product is NOT blacklisted and can be downloaded.
        False if the product IS blacklisted and should not be downloaded.
    """
    safe = os.path.basename(safe_full_path)
    ticket_path = os.path.join(whichquarantinedir(archive=archive), safe)
    logging.debug("Checking for quarantine ticket: %s", ticket_path)

    if os.path.exists(ticket_path):
        with open(ticket_path) as fid:
            num_attempts = len(fid.readlines())

        if num_attempts >= 10:
            logging.warning(
                "%s is blacklisted after %d failed attempts.",
                safe,
                num_attempts,
            )
            return False  # Do not download

    return True  # OK to download


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Test if a product is blacklisted."
    )
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        "--inputsafe",
        action="store",
        required=True,
        help="SAFE path to check (e.g., S1A_IW_...SAFE)",
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)-5s %(message)s",
            datefmt="%d/%m/%Y %H:%M:%S",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-5s %(message)s",
            datefmt="%d/%m/%Y %H:%M:%S",
        )

    can_be_downloaded = test_quarantine_before_download(
        args.inputsafe, archive="datawork"
    )

    if can_be_downloaded:
        logging.info("Product '%s' is OK to download.", args.inputsafe)
    else:
        logging.info(
            "Product '%s' is BLACKLISTED. Do not download.", args.inputsafe
        )


if __name__ == "__main__":
    main()
