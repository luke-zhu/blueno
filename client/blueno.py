# TODO: Keep client/blueno.py cluster/register/blueno.py. In the future,
#  more should be done to version this file properly.
import io
import time
from typing import Dict, Any, List, BinaryIO
from urllib.parse import urljoin

import requests


class PlatformError(Exception):
    pass


class PlatformClient(object):
    """
    Client for loading data into the platform.
    """
    retry_limit = 5

    def __init__(self,
                 server: str,
                 email: str,
                 password: str):
        self.server = server
        self.email = email
        self.__password = password
        self.__access_token = self.__updated_access_token()

    def list_datasets(self) -> List[Dict]:
        """
        Lists all datasets available to the team.

        :return: a list of Python dictionaries with
            the names of the datasets and other dataset metadata available.
        :raises PlatformError: if the action fails
        """
        res = self._request(
            'get',
            urljoin(self.server, '/datasets/'),
        )
        return res.json()['datasets']

    def create_dataset(self,
                       name: str,
                       description: str = None,
                       info: Dict = None) -> bool:
        """
        Creates a dataset with the given name.

        :param name: the name of the dataset. This must be unique.
        :param description: a description of the dataset
        :param info: other information to be included about the dataset,
            this object must be JSON-serializable
        :return: true if a new dataset is created, false if it already exists.
        :raises PlatformError: if the creation fails for another reason
        """
        if info is None:
            info = {}
        else:
            info = info.copy()
        if description:
            info['description'] = description
        payload = {
            'info': info,
        }
        res = self._request(
            'put',
            urljoin(self.server, f'/datasets/{name}'),
            json=payload,
        )

        if res.status_code == 200:
            return True
        if res.status_code == 409:
            return False
        raise PlatformError(
            f"Failed to create dataset {name}"
            f" (CODE={res.status_code} DATA={res.text})")

    def delete_dataset(self,
                       name: str) -> bool:
        """
        Deletes the dataset with the given name.

        To delete a dataset, all samples must be deleted first.
        # TODO: This is not good default behavior and should be changed.

        :param name: the name of the dataset to delete

        :return: true if the dataset is successfully deleted, false if
            it has already been deleted
        :raises PlatformError: if the deletion fails for another reason
        """
        res = self._request(
            'delete',
            urljoin(self.server, f'/datasets/{name}'),
        )
        if res.status_code == 200:
            return True
        if res.status_code == 404:
            return False
        raise PlatformError(
            f"Failed to delete dataset {name}"
            f" (CODE={res.status_code} DATA={res.text})")

    def list_samples(self, dataset: str) -> List[Dict]:
        """
        Lists the samples in the dataset.

        :param dataset: the name of a datset.
        :return: a list of dictionaries containing the names of the
            samples and additional metadata.
        :raises PlatformError: if an unexpect failure occurs
        """
        res = self._request(
            'get',
            urljoin(self.server, f'/datasets/{dataset}/samples/'),
        )
        if res.status_code == 200:
            return res.json()['samples']
        raise PlatformError(
            f"Could not list samples"
            f" (CODE={res.status_code} DATA={res.text})")

    def create_sample(self,
                      name: str,
                      dataset: str,
                      data_url: str,
                      data_content: BinaryIO,
                      image_type: str = None,
                      label: Any = None,
                      split: str = None,
                      other_info: Dict[str, Any] = None) -> bool:
        """
        Creates a sample from the provided info and data.

        This both uploads data and registers the sample.

        :param name: the name of the sample. This must be unique within
            the dataset.
        :param dataset: the name of the dataset to register the sample in.
            Dataset names must be unique within a team.
        :param data_url: the internal URL of the data
        :param data_content: the file content to upload to the data_url
        :param image_type: the type of image to generate from the data. If
            this is None, then no image is created.
        :param label: the class/target of the sample. This must be a JSON
            serializable object.
        :param split: 'training', 'test', or 'validation'
        :param other_info: other info about the sample to
            store in the platform's database
        :return: true if a new sample is created, false if the sample already
            exists
        """
        # TODO: New data shouldn't be uploaded if the sample already exists.
        self.upload_sample(data_url, data_content)
        return self.register_sample(
            name,
            dataset,
            data_url,
            validate=False,
            image_type=image_type,
            label=label,
            split=split,
            other_info=other_info,
        )

    def register_sample(self,
                        name: str,
                        dataset: str,
                        data_url: str,
                        validate: bool = True,
                        image_type: str = None,
                        label: Any = None,
                        split: str = None,
                        other_info: Dict[str, Any] = None) -> bool:
        """
        Registers the sample in the platform.

        :param name: the name of the sample. This must be unique within
            the dataset.
        :param dataset: the name of the dataset to register the sample in.
            Dataset names must be unique within a team.
        :param data_url: the internal URL of the data
        :param validate: if True, checks to see whether the
            data exists at the data_url
        :param image_type: the type of image to generate from the data. If
            this is None, then no image is created.
        :param label: the class/target of the sample. This must be a JSON
            serializable object.
        :param split: 'training', 'test', or 'validation'
        :param other_info: other info about the sample to
            store in the platform's database

        :return: true if a new sample was registered, false if a sample
            with the same name already exists
        :raises PlatformError: if an internal server error occurs
        """
        # 1. Prepare the payload options
        if other_info is None:
            info = {}
        else:
            info = other_info.copy()
        if data_url:
            info['data'] = {
                'url': data_url
            }
        if image_type:
            info['image'] = {
                'type': image_type,
            }
        info['label'] = label
        info['split'] = split

        payload = {
            'validate': validate,
            'info': info,
        }

        # 2. Make a request to create the sample
        res = self._request(
            'put',
            urljoin(self.server, f'/datasets/{dataset}/samples/{name}'),
            json=payload,
        )

        if res.status_code == 200:
            return True
        if res.status_code == 409:
            return False
        raise PlatformError(
            f"Failed to create sample {name} in {dataset}"
            f" (CODE={res.status_code} DATA={res.text})")

    def upload_sample(self, data_url: str, data_content: BinaryIO):
        """
        Uploads the file content to the data url.

        :param data_url: the internal url of the sample
        :param data_content: a file-like object
        :raises PlatformError: if the upload fails
        """
        files = {
            'file': (data_url, data_content),
        }
        url = urljoin(self.server, '/data/upload')
        res = self._request('post', url,
                            params={
                                'url': data_url,
                            },
                            files=files)
        # TODO: Explain that if stale file handle error, user needs to
        #  restart the NFS server.
        if res.status_code not in (200, 201):
            raise PlatformError(
                f"Failed to upload data {data_url}"
                f" (CODE={res.status_code} DATA={res.text})")

    def download_sample(self, data_url) -> io.BytesIO:
        """
        Downloads sample data from the platform.

        :param data_url: the internal url of the sample
        :raises PlatformError: if the download fails
        """
        res = self._request(
            'get',
            urljoin(self.server, f'/data/download'),
            params={
                'url': data_url,
            },
        )
        if res.status_code not in (200, 201):
            raise PlatformError(
                f"Failed to download data at {data_url}"
                f" (CODE={res.status_code} DATA={res.text})")
        return io.BytesIO(res.content)

    def delete_sample(self,
                      name: str,
                      dataset: str,
                      purge=False) -> bool:
        """Deletes the sample in the dataset

        :param name: the name of the sample
        :param dataset: the dataset the sample is in
        :param purge: whether to also purge the associated
            data (in GCS, S3, ...)
        :return: true of the sample was deleted, false if the sample
            did not exist
        :raises PlatformError: if an unexpected error occured
        """
        payload = {
            'purge': purge,
        }
        res = self._request(
            'delete',
            urljoin(self.server, f'/datasets/{dataset}/samples/{name}'),
            json=payload,
        )

        if res.status_code == 200:
            return True
        if res.status_code == 404:
            return False
        raise PlatformError(f"Failed to delete sample {name} in {dataset}"
                            f" (CODE={res.status_code} DATA={res.text})")

    def _request(self, method, url, **kwargs) -> requests.Response:
        """
        Wrapper around requests.request() that handles authentication
        and retries.

        Do not use requests.request() or its variant (requests.get())
        if this method is a better choice.
        """
        if 'headers' not in kwargs:
            kwargs['headers'] = {
                'Authorization': 'Bearer {}'.format(self.__access_token)
            }

        count = 0
        while True:
            try:
                res = requests.request(method,
                                       url,
                                       **kwargs)
            except (requests.ConnectionError, requests.Timeout) as e:
                if count < self.retry_limit:
                    print(f'network error for request {method} {url}: {e}')
                    count += 1
                    time.sleep(2 ** count)
                else:
                    raise e
            else:
                if res.status_code >= 500:
                    if count < self.retry_limit:
                        print(
                            f'server error for request {method} {url}:'
                            f' {res.reason}')
                        count += 1
                        time.sleep(2 ** count)
                    else:
                        res.raise_for_status()
                else:
                    break  # break out of the while loop

        assert res.status_code < 500
        if res.status_code == 401:
            self.__access_token = self.__updated_access_token()
            # Update the access token for the next request
            kwargs['headers']['Authorization'] = 'Bearer {}'.format(
                self.__access_token)
            return self._request(method, url,
                                 **kwargs)
        return res

    def __updated_access_token(self) -> str:
        res = requests.post(
            urljoin(self.server, '/login'),
            json={
                'email': self.email,
                'password': self.__password,
            }
        )
        if res.status_code == 200:
            return res.json()['access_token']
        else:
            raise PlatformError(
                f"Failed to authenticate"
                f" (CODE={res.status_code} DATA={res.text})")
