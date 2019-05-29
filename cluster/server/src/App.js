import React, {Component} from 'react';
import {Form, Icon, Input, Layout, Menu} from 'antd';
import {BrowserRouter, Link, Route} from "react-router-dom";
import './App.css'
import DatasetPage from "./DatasetPage";
import {login, isLoggedIn, logout} from "./api";
import SetupPage from "./SetupPage";
import AdminPage from "./AdminPage";
import OverviewPage from "./OverviewPage";

/**
 * Handles user authentication.
 *
 * Access tokens are kept in local storage. All API calls should use the
 * access token in local storage and redirect to this page if a 401
 * error occurs.
 */
class LoginPage extends Component {
  constructor(props) {
    super(props);

    this.state = {
      email: '',
      password: '',
      loginError: '',
      loginSuccess: '',
    };
    this.login = this.login.bind(this);
  }

  async login() {
    try {
      await login(this.state.email, this.state.password);
      this.setState({
        loginError: '',
        loginSuccess: 'Successfully logged in',
      });
      window.location.replace('/ui/'); // redirect to home
    } catch (e) {
      console.log(e.response.data);
      this.setState({
        loginError: e.response.data['message'],
      })
    }
  }

  render() {
    return (
        <Form style={{padding: 15}}>
          <Form.Item label="Email Address">
            <Input
                onChange={e => this.setState({email: e.target.value})}
                onPressEnter={this.login}
                addonAfter={<Icon type="mail"
                                  theme="filled"/>}/>
          </Form.Item>
          <Form.Item label="Password">
            <Input.Password onPressEnter={this.login}
                            onChange={e => this.setState({password: e.target.value})}
                            addonAfter={<Icon type="lock"
                                              theme="filled"/>}/>

          </Form.Item>
          <span style={{color: 'red'}}>
                    {this.state.loginError}
                </span>
          <span style={{color: 'green'}}>
                    {this.state.loginSuccess}
                </span>
        </Form>
    )
  }
}

/**
 * The ReactDOM entrypoint component.
 *
 * This class renders the top-level navbar.
 */
class App extends Component {
  render() {
    let rightMenuItem;
    if (isLoggedIn()) {
      rightMenuItem = (
          <Menu.SubMenu
              style={{float: 'right'}}
              title={<span>
                <Icon type="profile"/>
                <Icon type="caret-down"/>
              </span>}
          >
            <Menu.Item>
              <Link to="/ui/admin">Admin</Link>
            </Menu.Item>
            <Menu.Item onClick={logout}>
              Log Out
            </Menu.Item>
          </Menu.SubMenu>
      )
    } else {
      rightMenuItem = (
          <Menu.Item style={{float: 'right'}}>
            <Link to="/ui/login">Log In</Link>
          </Menu.Item>
      )
    }

    return (
        <BrowserRouter>
          <Layout style={{height: '100vh'}}>

            {/* Top-level navbar */}
            <Layout.Header>
              <Menu mode="horizontal" theme="dark"
                    style={{lineHeight: '64px'}}>
                <Menu.Item>
                  <Link to="/ui/">Blueno</Link>
                </Menu.Item>
                {/*<Menu.Item>*/}
                {/*  <Link to="/ui/overview">Overview</Link>*/}
                {/*</Menu.Item>*/}
                <Menu.Item>
                  <a href="https://github.com/luke-zhu/blueno"><Icon
                      type="github"/></a>
                </Menu.Item>
                {rightMenuItem}
              </Menu>
            </Layout.Header>

            <Layout.Content>
              {/* Routes to pages */}
              <Route exact path="/" component={DatasetPage}/>
              <Route exact path="/ui/" component={DatasetPage}/>
              <Route exact path="/ui/login" component={LoginPage}/>
              <Route exact path="/ui/setup" component={SetupPage}/>
              <Route exact path="/ui/admin" component={AdminPage}/>
              <Route exact path="/ui/overview" component={OverviewPage}/>
            </Layout.Content>
          </Layout>
        </BrowserRouter>
    )
  }
}

export default App;
