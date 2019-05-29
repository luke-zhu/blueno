The server handles requests to create, get, or delete
datasets and samples.

The server entrypoint is `app/___init__.py`.
The frontend code is in `src/`.

## Environment Variables
As of 5/17/2019, there are 5 different environment
variables. All environment variables are placed in `app/env.py`.

Here are the names of the environment variables and descriptions:

`JWT_SECRET_KEY` (required): The HMAC secret used
to sign the JSON Web Tokens.

`FILESYSTEM_STORE_ROOT` (optional): The directory to
store FilesystemStore objects in.

- For example, if `FILESYSTEM_STORE_ROOT='/var/lib/platform`
  `file://blueno/data.npy` will be stored in the real
  filepath `/var/lib/platform/blueno/data.npy`.

`GOOGLE_APPLICATION_CREDENTIALS` (optional): The the file path of the JSON file that contains your Google Cloud Storage service account key
See [the GCP docs](https://cloud.google.com/docs/authentication/getting-started#setting_the_environment_variable) for more info.

`AZURE_STORAGE_ACCOUNT` (optional): the name of your Azure Storage Account

`AZURE_STORAGE_KEY` (optional): an access key to your Azure Storage Account 

## Info Column Schema
As of 5/29/2019, the following fields in the info column
are used by the app:

- data: Object
    - url: str: an internal URL
- image: Optional[Object]
    - url: str: an internal URL _prefix_
    - type: str: either "2D" or "3D"
    - count: int: the number of images of the sample
- split: Optional[str]: a split class tag to give the sample
- label: Optional[Union[str, int]]: the label of the sample
    
The image url field does not contain an extension. The
application determines the full URL from both the type
and the data URL.

In the future, the schema should be explicitly defined.