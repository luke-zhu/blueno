import React from 'react';
import {Form, Input, Layout, List, Pagination, Select,} from "antd";
import {
  countSamples,
  listDatasets,
  listSampleImages,
  listSamples
} from "./api";
import SampleCard from "./SampleCard";

/**
 * The main page of the UI.
 *
 * This page allows one to select different datasets and see images of the
 * samples. It also includes inputs for filtering and seeing more detailed
 * views of the data.
 */
class DatasetPage extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      datasets: [], // a list of dataset names
      selectedDataset: undefined, // the name of the selected dataset, sample info of the dataset is loaded the fields below
      samples: [],
      sampleImages: [],
      numSamples: 0,

      pageOffset: undefined, // used by the Pagination element to control which samples are loaded.
      prefix: '', // the prefix input value
      label: '', // the label input value
      split: '', // the split input value
    };

    this.datasetOnChange = this.datasetOnChange.bind(this);
    this.offsetOnChange = this.offsetOnChange.bind(this);
    this.updateSamples = this.updateSamples.bind(this);
  }

  async componentDidMount() {
    try {
      const datasets = await listDatasets();
      this.setState({
        datasets: datasets,
      })
    } catch (e) {
      console.log(e); // TODO: Render an error popup(?)
    }
  }

  async datasetOnChange(dataset) {
    try {
      // TODO: Show a loading icon while these network calls occur?
      const samples = await listSamples({
        dataset: dataset,
        limit: 16,
      });
      const sampleImages = await listSampleImages({
        dataset: dataset,
        limit: 16,
      });
      const count = await countSamples(dataset);
      this.setState({
        selectedDataset: dataset,
        samples: samples,
        sampleImages: sampleImages,
        numSamples: count,

        // We reset these fields below to their original state.
        pageOffset: 1,
        prefix: '',
        label: '',
        split: '',
      });
    } catch (e) {
      console.log(e); // TODO: Render an error popup(?)
    }
  };

  // handle a page change event
  async offsetOnChange(pageOffset) {
    const payload = {
      dataset: this.state.selectedDataset,
      limit: 16,
      offset: 16 * (pageOffset - 1),
      prefix: this.state.prefix,
      label: this.state.label,
      split: this.state.split,
    };
    const samples = await listSamples(payload);
    const sampleImages = await listSampleImages(payload);

    this.setState({
      samples: samples,
      sampleImages: sampleImages,
      pageOffset: pageOffset,
    });
  }

  // This is a time-consuming call to fetch new samples and images
  // from the server.
  async updateSamples() {
    const payload = {
      dataset: this.state.selectedDataset,
      limit: 16,
      offset: 16 * (this.state.pageOffset - 1),
      prefix: this.state.prefix,
      label: this.state.label,
      split: this.state.split,
    };
    const samples = await listSamples(payload);
    const sampleImages = await listSampleImages(payload);

    this.setState({
      samples: samples,
      sampleImages: sampleImages,
    });
  }

  render() {
    const datasetOptions = this.state.datasets.map(e => {
      return <Select.Option key={e.name}>{e.name}</Select.Option>;
    });

    const sampleCards = this.state.samples.slice(0, 16).map((e, i) => {
      return (
          // We set the key to such below so that the sample card properly updates
          // the SampleCard on dataset changes and page changes.
          <List.Item key={`${this.state.selectedDataset}-${e.name}`}>
            <SampleCard
                dataset={this.state.selectedDataset}
                sample={e}
                image={this.state.sampleImages[i]}
            />
          </List.Item>
      );
    });

    return (
        <Layout style={{height: '100%'}}>

          {/* The sider contains various inputs for altering */}
          {/* If the sider width is changed, change the Sample Card modal style too. */}
          <Layout.Sider width={240}
                        style={{background: '#fff', padding: 15}}>
            <Form>
              <Form.Item label="Dataset">
                <Select onChange={this.datasetOnChange}>
                  {datasetOptions}
                </Select>
              </Form.Item>

              <Form.Item label="Prefix">
                <Input value={this.state.prefix}
                       onChange={(e) => this.setState({prefix: e.target.value})}
                       onPressEnter={this.updateSamples}/>
              </Form.Item>

              <Form.Item label="Label">
                <Input value={this.state.label}
                       onChange={(e) => this.setState({label: e.target.value})}
                       onPressEnter={this.updateSamples}/>
              </Form.Item>

              <Form.Item label="Split">
                <Input value={this.state.split}
                       onChange={(e) => this.setState({split: e.target.value})}
                       onPressEnter={this.updateSamples}/>
              </Form.Item>

              <Form.Item>
                <Pagination
                    current={this.state.pageOffset}
                    pageSize={1}
                    total={Math.ceil(this.state.numSamples / 16)}
                    onChange={this.offsetOnChange}
                    simple={true}
                    size="small"
                />
              </Form.Item>
            </Form>
          </Layout.Sider>

          <Layout.Content style={{padding: '0 50px'}}>
            <List grid={{
              gutter: 16,
              xs: 1,
              sm: 2, md: 2,
              lg: 4, xl: 4, xxl: 4
            }}>
              {sampleCards}
            </List>
          </Layout.Content>
        </Layout>
    );
  }
}

export default DatasetPage;