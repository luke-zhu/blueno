import React from "react";

import {
  Button,
  Card,
  Form,
  Icon,
  InputNumber,
  Modal,
  Popover,
  Slider
} from "antd";
import {getImagesForSample} from "./api";

// the number of image URLs to prefetch for a selected single 3D sample
const NUM_IMAGE_URLS = 32;
// the sensitivity of the wheel when scrolling through the detail view of a 3D image
const WHEEL_SENSITIVITY = 10;

/**
 * The Card component displaying the image of a sample and more.
 *
 * This component displays an image of a single sample and contains
 * buttons to display more information about the sample.
 *
 * These sample cards are displayed from DatasetPage.
 */
class SampleCard extends React.Component {

  // props: dataset, sample, image
  // There are currently 3 props, all required: dataset, sample, image
  // dataset is the name of the dataset
  // sample is an object with the field 'name', 'created_at', and 'last_updated'.
  // sample can also have an image field.
  // image is the preview URL of the sample which is displayed on the initial card.
  // TODO: proptypes


  constructor(props) {
    super(props);
    this.state = {
      visible: false, // whether the modal is visible
      imageURLs: Array(NUM_IMAGE_URLS).fill(null), // images of sample, there will only be 1 for 2D images
      center: 0, // the offset of the image stored at index (NUM_IMAGE_URLS / 2) in imageURLs
      offset: 0, // the offset of the currently viewed image
      wheelDelta: 0, // used to make wheel scrolling through a 3D image less sensitive and more smooth
    };

    this.showModal = this.showModal.bind(this);
    this.hideModal = this.hideModal.bind(this);
    this.offsetOnChange = this.offsetOnChange.bind(this);
    this.offsetOnWheel = this.offsetOnWheel.bind(this);
  }

  async showModal() {
    this.setState({visible: true});
    await this.updateImageURLs(this.state.offset);
  }

  hideModal() {
    this.setState({visible: false})
  }


  /**
   * Fetches image urls for the sample from the server and updates the state.
   *
   * Images in the range [newOffset, newOffset + NUM_IMAGE_URLS) will be fetched.
   * Less than NUM_IMAGE_URLS may be fetched if newOffset is too high.
   *
   * @param newOffset - the offset of the FIRST image to fetch, must be >= 0
   **/
  async updateImageURLs(newOffset) {
    // TODO: Should network errors result in a popup message to the user?
    const imageURLs = await getImagesForSample(
        this.props.dataset,
        this.props.sample.name,
        NUM_IMAGE_URLS,
        newOffset,
    );

    this.setState({
      imageURLs: imageURLs,
      center: newOffset + NUM_IMAGE_URLS / 2,
    })
  }

  static shouldFetchImages(newOffset, currentCenter) {
    // we try to fetch image urls early so that scrolling in both directions
    // stays smooth
    return Math.abs(newOffset - currentCenter) >= (NUM_IMAGE_URLS / 2 - 2);
  }

  async offsetOnChange(newOffset) {
    this.setState({
      offset: newOffset,
    });
    if (SampleCard.shouldFetchImages(newOffset, this.state.center)) {
      await this.updateImageURLs(Math.max(0, newOffset - NUM_IMAGE_URLS / 2))
    }
  }

  // smoothly handle an onwheel event and update the offset and wheel delta state
  async offsetOnWheel(event) {
    if (!this.state.imageURLs || this.state.imageURLs.length === 1) {
      return;
    }

    let newWheelDelta = this.state.wheelDelta + event.deltaY;
    let newOffset = this.state.offset;
    if (newWheelDelta >= WHEEL_SENSITIVITY) {
      newWheelDelta = 0;
      newOffset += 1;

      this.setState({
        offset: newOffset,
        wheelDelta: newWheelDelta,
      });

      if (SampleCard.shouldFetchImages(newOffset, this.state.center)) {
        await this.updateImageURLs(Math.max(0, newOffset - NUM_IMAGE_URLS / 2))
      }
    } else if (newWheelDelta <= -WHEEL_SENSITIVITY && newOffset > 0) {
      newWheelDelta = 0;
      newOffset -= 1;

      this.setState({
        offset: newOffset,
        wheelDelta: newWheelDelta,
      });

      if (SampleCard.shouldFetchImages(newOffset, this.state.center)) {
        await this.updateImageURLs(Math.max(0, newOffset - NUM_IMAGE_URLS / 2))
      }
    } else {
      this.setState({
        // we cap the wheelDelta so that overscrolling has no effect
        wheelDelta: Math.max(Math.min(newWheelDelta, WHEEL_SENSITIVITY), -WHEEL_SENSITIVITY),
      })
    }
  }

  render() {
    // Compute the image to render from the image offset state.
    const imageIndex = this.state.offset - this.state.center + NUM_IMAGE_URLS / 2;
    let imageURL;
    if (this.state.imageURLs) {
      imageURL = this.state.imageURLs[imageIndex];
    } else {
      imageURL = null;
    }

    // Generate the info popover content.
    let infoContent;
    if ('info' in this.props.sample) {
      infoContent = (
          <div>
            <p>Created At: {this.props.sample['created_at']}</p>
            <p>Last Updated: {this.props.sample['last_updated']}</p>
            <pre>{JSON.stringify(this.props.sample['info'], null, 2)}</pre>
          </div>
      );
    } else {
      infoContent = (
          <div>
            <p>Created At: {this.props.sample['created_at']}</p>
            <p>Last Updated: {this.props.sample['last_updated']}</p>
          </div>
      );
    }

    // If there are multiple images of the sample, then we also want to display
    // offset controls
    let offsetContent;
    try {
      if (this.props.sample.info.image.count > 1) {
        offsetContent = (
            <div>
              <Slider min={0} max={this.props.sample.info.image.count - 1}
                      value={this.state.offset}
                      onChange={this.offsetOnChange}
              />
              <Form layout="inline">
                <Form.Item label="Offset">
                  <InputNumber min={0}
                               max={this.props.sample.info.image.count - 1}
                               value={this.state.offset}
                               onChange={this.offsetOnChange}
                  />
                </Form.Item>
              </Form>
            </div>
        );
      }
    } catch (e) {
      offsetContent = null;
    }

    return (
        <Card title={this.props.sample.name}
              style={{
                height: 300, // cards must be fixed size otherwise the DatasetPage grid list renders very poorly
              }}
              bodyStyle={{
                padding: 5, // we set the padding so the icons are close enough to the image
              }}
              cover={
                // These styles get the image to fill the card space if too small but not
                // overflow if too large.
                <div style={{height: 200, width: '100%'}}>
                  <img
                      src={this.props.image}
                      style={{
                        objectFit: 'contain',
                        height: '100%',
                        width: '100%',
                        padding: 10,
                      }}
                  />
                </div>
              }>

          {/* Below here is the body of the card*/}
          <div style={{
            display: 'flex',
            flexDirection: 'row',
          }}>

            {/* The popover is inside the body but only the button is displayed inside of the card.*/}
            <Popover content={infoContent}
                     title="Sample Info">
              <Button><Icon type="info-circle"/></Button>
            </Popover>

            <Button onClick={this.showModal}>
              <Icon type="arrows-alt"/>
            </Button>

            {/* The modal is inside of the body but displayed outside of the card.*/}
            {/* If the form width is changed, this should be changed too. */}
            <Modal
                title={`${this.props.sample.name}`}
                style={{top: 20, left: 300, position: 'fixed'}}
                visible={this.state.visible}
                onOk={this.hideModal}
                onCancel={this.hideModal}
            >
              <Card
                  cover={
                    <img
                        src={imageURL}
                        onWheel={this.offsetOnWheel}
                        alt={this.props.sample.name}
                        style={{
                          objectFit: 'contain',
                          maxWidth: '100%',
                          maxHeight: '60vh',
                        }}
                    />
                  }
              >
                {offsetContent}
              </Card>
            </Modal>
          </div>
        </Card>
    )
  }
}

export default SampleCard;