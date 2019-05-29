import React from 'react';
import {Button, Checkbox, Form, Input, Layout} from "antd";
import {register} from "./api";
import {DATASETS} from "./datasets";


/**
 * The Admin Page allows to user to register additional datasets.
 *
 * In the future, addition ad
 **/
export default class AdminPage extends React.Component {
  state = {
    email: '',
    registerResponses: [],
    password: '',
    setupError: undefined,
  };

  handleSubmit = async () => {
    try {
      const r = await register(
          this.state.email,
          this.state.password,
          this.state.datasets);
      this.setState({
        registerResponses: r.data.datasets,
      })
    } catch (e) {
      if (e.response) {
        this.setState({
          setupError: e.response.data['message'],
        })
      } else {
        console.log(e);
      }
    }
  };

  handleDatasetCBChange = checkedDatasets => {
    this.setState({
      datasets: checkedDatasets,
    });
  };


  render() {
    const formattedResponses = this.state.registerResponses.map(e => {
          const color = (e.status === 'failed') ? 'orange' : 'green';
          return <p style={{color: color}}>{e.message}</p>;
        }
    );

    return (
        <Layout style={{padding: '5%'}}>
          <Form>
            <h1>Step 1: Re-enter your Username and Password</h1>
            <Form.Item label="Email">
              <Input
                  onChange={e => this.setState({email: e.target.value})}
              />
            </Form.Item>
            <Form.Item label="Password">
              <Input.Password
                  onChange={e => this.setState({password: e.target.value})}
              />
            </Form.Item>
            <h1>Step 2: Select a Few Datasets</h1>
            <p>
              These public datasets will be downloaded in the background after
              submitting this form.
            </p>
            <Form.Item>
              <Checkbox.Group options={DATASETS}
                              onChange={this.handleDatasetCBChange}/>
              <span style={{color: 'red'}}>{this.state.setupError}</span>
              <div>{formattedResponses}</div>
            </Form.Item>
            <Form.Item>
              <Button type="primary" onClick={this.handleSubmit}>
                Submit
              </Button>
            </Form.Item>
          </Form>
        </Layout>
    );
  }
}