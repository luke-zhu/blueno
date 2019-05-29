/**
 * Methods for making API calls to the server.
 *
 * Since the API is currently undocumented and subject to change, all server
 * API requests should be put here.
 */
import axios from 'axios';

const EMAIL = 'user-email';
const REFRESH_TOKEN = 'user-refresh-token';
const ACCESS_TOKEN = 'user-token';

/**
 * Stores the refresh and access token corresponding to the email and
 * password in local storage.
 *
 * @param email
 * @param password
 * @returns {Promise<*>}
 */
export async function login(email, password) {
  const response = await axios.post('/login', {
    email,
    password,
  });
  const refreshToken = response.data['refresh_token'];
  const accessToken = response.data['access_token'];

  localStorage.setItem(EMAIL, email);
  localStorage.setItem(REFRESH_TOKEN, refreshToken);
  localStorage.setItem(ACCESS_TOKEN, accessToken);
}

export function isLoggedIn() {
  return localStorage.getItem(ACCESS_TOKEN) !== null;
}

export function logout() {
  localStorage.removeItem(EMAIL);
  localStorage.removeItem(REFRESH_TOKEN);
  localStorage.removeItem(ACCESS_TOKEN);
  window.location.reload();
}

/**
 * Returns true if a user has already been created, false otherwise.
 */
export async function isInitialized() {
  const response = await axios.get('/setup');
  return response.data['initialized'];
}


/**
 * Creates a new user with the given email and password. Starts jobs
 * to prepare the datasets.
 *
 * This endpoint only works if a new user has not been created yet.
 *
 * @param email {string}
 * @param password {string}
 * @param datasets {Array<string>} a list of dataset names
 * @returns {Promise<AxiosResponse<any>>}
 */
export async function setup(email, password, datasets) {
  await axios.post('/setup', {
    email,
    password,
  });

  await login(email, password);

  return await register(email, password, datasets);
}

export async function register(email, password, datasets) {
  return await wrappedRequest({
    url: '/register',
    method: 'post',
    data: {
      email,
      password,
      datasets,
    }
  });
}


/**
 * Wrapper over axios.request for accessing protected endpoints.
 *
 * If the refresh token has expired, this will redirect to the login page.
 *
 * @param config an Axios config
 * @returns {Promise<void>} an axios Response
 */
async function wrappedRequest(config) {
  const accessToken = localStorage.getItem(ACCESS_TOKEN);

  // 1. Initial request
  try {
    return await axios.request(Object.assign({
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      }
    }, config))
  } catch (err) {
    // 2. If the error is related to authentication, try to update the
    // access token and make a new request
    if (err.response && (err.response.status === 401 || err.response.status === 422)) {
      try {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN);
        const response = await axios.post('/refresh', null, {
          headers: {
            'Authorization': `Bearer ${refreshToken}`,
          }
        });

        const newAccessToken = response.data['access_token'];
        localStorage.setItem(ACCESS_TOKEN, newAccessToken);

        return await axios.request(Object.assign({
          headers: {
            'Authorization': `Bearer ${newAccessToken}`,
          }
        }, config))
      } catch (err) {
        // 3. The refresh token has expired so request a login.
        if (!await isInitialized()) {
          window.location.replace('/ui/setup');
        } else {
          window.location.replace('/ui/login');
        }
      }
    } else {
      throw err;
    }
  }
}

/**
 * Lists all datasets.
 *
 * @returns {Promise<*>} a list of dataset info objects
 */
export async function listDatasets() {
  const response = await wrappedRequest({url: '/datasets/'});
  return response.data['datasets'];
}

/**
 * Lists samples in the dataset.
 *
 * @param dataset
 * @param limit - the number of samples to display
 * @param offset - the index pageOffset of the first sample to get
 * @param prefix - sample name prefix to filter by
 * @param label - the training label or target of the sample
 * @param split - the split class of the sample
 * @returns {Promise<*>} a list of sample info objects
 */
export async function listSamples({
                                    dataset,
                                    limit = null,
                                    offset = 0,
                                    prefix = '',
                                    label = '',
                                    split = '',
                                  }) {
  const params = {
    limit: limit,
    offset: offset,
    prefix: prefix,
    label: label,
    split: split,
  };
  const response = await wrappedRequest({
    url: `/datasets/${dataset}/samples/`,
    params: params,
  });
  return response.data['samples'];
}


export async function countSamples(dataset) {
  const response = await wrappedRequest({
    url: `/datasets/${dataset}/samples/count`,
  });
  return response.data['count'];
}

/**
 * Lists signed URLs to images in the dataset.
 *
 * @param dataset
 * @param limit - the number of samples to display
 * @param offset - the index pageOffset of the first sample to get
 * @param prefix - sample name prefix to filter by
 * @param label - the training label or target of the sample
 * @param split - the split class of the sample
 * @returns {Promise<void>} a list of URLs
 */
export async function listSampleImages({
                                         dataset,
                                         limit = null,
                                         offset = 0,
                                         prefix = '',
                                         label = '',
                                         split = '',
                                       }) {
  const params = {
    limit: limit,
    offset: offset,
    prefix: prefix,
    label: label,
    split: split,
  };
  const response = await wrappedRequest({
    url: `/datasets/${dataset}/samples/images`,
    params: params,
  });
  return response.data['images'];
}

/**
 * Get signed urls to all images associated to the sample.
 *
 * @returns {Promise<*>} a list of URLs to images of the sample
 */
export async function getImagesForSample(dataset,
                                         sample,
                                         limit,
                                         offset) {
  const params = {
    limit: limit,
    offset: offset,
  };
  const response = await wrappedRequest({
    url: `/datasets/${dataset}/samples/${sample}/images`,
    params: params,
  });
  return response.data['images'];
}