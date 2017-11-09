import sys
from neo.Settings import settings
from prompt_toolkit import prompt
import requests
from tqdm import tqdm
import tarfile
import shutil
import os


def BootstrapBlockchain():

    current_chain_dir = settings.LEVELDB_PATH

    bootstrap_file = settings.BOOTSTRAP_FILE

    if bootstrap_file is None:
        print("no bootstrap file specified.  Please update your configuration file.")
        sys.exit(0)

    print("This will overwrite any data currently in %s.\nType 'confirm' to continue" % current_chain_dir)

    confirm = prompt("[confirm]> ", is_password=False)

    if confirm == 'confirm':
        return do_bootstrap()

    print("bootstrap cancelled")
    sys.exit(0)


def do_bootstrap():

    bootstrap_file = settings.BOOTSTRAP_FILE
    destination_dir = settings.LEVELDB_PATH

    success = False

    print('will download file %s ' % bootstrap_file)
    print('')
    tmp_file_name = './Chains/bootstrap.tar.gz'
    tmp_chain_name = 'tmpchain'

    try:
        response = requests.get(bootstrap_file, stream=True)

        response.raise_for_status()

        # Total size in bytes.
        total_size = int(response.headers.get('content-length', 0))

        chunkSize = 1024
        with open(tmp_file_name, 'wb') as f:
            pbar = tqdm(unit="B", total=total_size)
            for chunk in response.iter_content(chunk_size=chunkSize):
                if chunk:  # filter out keep-alive new chunks
                    pbar.update(len(chunk))
                    f.write(chunk)

        print("download complete")

        if os.path.exists(destination_dir):

            try:
                shutil.rmtree(destination_dir)
            except Exception as e:

                print("coludnt remove existing dir: %s %s" % (e, destination_dir))
                sys.exit(0)

        print("Opening archive %s " % tmp_file_name)

        # open file
        tar = tarfile.open(tmp_file_name)

        # get the name of the chain directory in the archive
        datadir = tar.getnames()[0]

        print("Extracting to %s " % tmp_chain_name)
        tar.extractall(tmp_chain_name)

        # construct current path in archive of Chain dir
        chaindata_dir = "%s/%s" % (tmp_chain_name, datadir)

        print("Moving to %s " % destination_dir)
        # move chain dir in archive into LEVELDB_PATH
        shutil.move(chaindata_dir, destination_dir)

        print("closing archive")
        tar.close()

        success = True

    except Exception as e:
        print("Could not download: %s " % e)

    finally:

        print("cleaning up %s " % tmp_file_name)
#        os.remove(tmp_file_name)
        print("cleaning up %s " % tmp_chain_name)
        shutil.rmtree(tmp_chain_name)

    if success:
        print("Successfully downloaded bootstrap chain!")

    sys.exit(0)
