import sys
from neo.Settings import settings
from prompt_toolkit import prompt
import requests
from tqdm import tqdm
import tarfile
import shutil
import os


def BootstrapBlockchainFile(target_dir, download_location, bootstrap_name, require_confirm=True):
    if download_location is None:
        print("no bootstrap location file specified. Please update your configuration file.")
        sys.exit(0)

    if require_confirm:
        print("This will overwrite any data currently in %s.\nType 'confirm' to continue" % target_dir)
        confirm = prompt("[confirm]> ", is_password=False)
        if confirm == 'confirm':
            return do_bootstrap(download_location, bootstrap_name, target_dir)
    else:

        return do_bootstrap(download_location,
                            bootstrap_name,
                            target_dir,
                            tmp_file_name=os.path.join(settings.DATA_DIR_PATH, 'btest.tar.gz'),
                            tmp_chain_name='btestchain')

    print("bootstrap cancelled")
    sys.exit(0)


def do_bootstrap(download_location, bootstrap_name, destination_dir, tmp_file_name=None, tmp_chain_name='tmpchain'):
    if tmp_file_name is None:
        tmp_file_name = os.path.join(settings.DATA_DIR_PATH, 'bootstrap.tar.gz')

    success = False

    try:
        source = requests.get(download_location)
        source.raise_for_status()
        source_json = source.json()
        response = requests.get(source_json[bootstrap_name], stream=True)
        response.raise_for_status()

        print('will download file %s ' % source_json[bootstrap_name])
        print('')

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
                print("couldn't remove existing dir: %s %s" % (e, destination_dir))
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
        print("cleaning up %s " % tmp_chain_name)
        if os.path.exists(tmp_chain_name):
            shutil.rmtree(tmp_chain_name)

    if success:
        print("Successfully downloaded bootstrap chain!")

    sys.exit(0)
