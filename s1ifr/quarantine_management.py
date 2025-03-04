import datetime
import logging
import os
import shutil
import pdb

from s1ifr.SAFEsortingfunctions import whichquarantinedir


def quarantine_ticket(safe_full_path, other_archive):
    """
    rm the corrupted safe and write into a ticket the date of the processing
    (add the date if the ticket already exists)
    """
    base_safe = os.path.basename(safe_full_path)
    path_ticket = os.path.join(whichquarantinedir(archive=other_archive),base_safe)
    if os.path.exists(path_ticket):
        fid = open(path_ticket, "a")

    else:
        fid = open(path_ticket, "w")
    fid.write(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M%S") + "\n")
    fid.close()
    remove_safe_from_disk(safe_full_path)


def remove_safe_from_disk(safe_full_path):
    if os.path.isfile(safe_full_path):
        os.remove(safe_full_path)
    else:
        shutil.rmtree(safe_full_path)
    logging.info("%s deleted", safe_full_path)


def test_quarantine_before_download(safe_full_path, archive) -> bool:
    """
    if the number of lines in the ticket in quarantine if >10 then no download
    :returns
        is_black_listed (bool): True -> means that the product has been downloaded 10 times and 10 times the product could not be sorted
    """
    flag_go_download = True
    safe = os.path.basename(safe_full_path)
    associated_potential_quarantine_ticket = os.path.join(
        whichquarantinedir(archive=archive), safe
    )
    logging.debug(
        "quarantine potential file %s", associated_potential_quarantine_ticket
    )
    if os.path.exists(associated_potential_quarantine_ticket):
        fid = open(associated_potential_quarantine_ticket)
        data = fid.readlines()
        fid.close()
        if len(data) >= 10:
            flag_go_download = False
            logging.info("%s is black listed for download", safe)

    return flag_go_download


def main():
    import argparse

    parser = argparse.ArgumentParser(description="test product black list")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        "--inputsafe",
        action="store",
        required=True,
        help="SAFE path to sort (could be SAFE.zip)",
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

    flag_go_download = test_quarantine_before_download(
        args.inputsafe, archive="datawork"
    )
    logging.info("flag_go_download : %s", flag_go_download)


if __name__ == "__main__":
    main()
