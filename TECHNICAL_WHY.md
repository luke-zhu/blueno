# Common Data and Infrastructure Problems that Blueno Addresses

### Overview
Blueno can improve the productivity of a deep learning team immensely. It does so by addressing data problems in the field which are estimated to take [80%](https://www.infoworld.com/article/3228245/the-80-20-data-science-dilemma.html) or even
[90%](https://www.technologyreview.com/s/612897/this-is-why-ai-has-yet-to-reshape-most-businesses/) of a ML practitioner’s time.

In particular, the Blueno-specific apps solve the problem of getting image data into a format that can be fed into a deep learning model.
Even for public datasets like ImageNet, this can take more than a week to do.
The open-source apps that Blueno sets up (Kubernetes, NFS-Ganesha, Postgres) and the apps that Blueno make easy to set up (Jupyter, Mlflow) allow you to reach high levels of productivity over the course of a 1-3 month long deep learning project.

We believe that the Blueno setup leads to high-function teams that do the following:
1. Spend most of their time writing code or thinking of ways to improve their models.
2. Identify training jobs worth running from experiment data and visualizations.
3. Run dozens of training jobs at the same time
4. Add tools on top of their infrastructure over time to become even more effective.

You probably are not as optimistic as us so we’ve created this document listing common data/infra problems which motivated us to build this project. If this doesn’t persuade you to start with Blueno, hopefully it does make you put more thought into your ML infrastructure.

   * [How Blueno Increases Deep Learning Productivity](#how-blueno-increases-deep-learning-productivity)
      * [Overview](#overview)
         * [Assumptions](#assumptions)
         * [Blueno's Cons](#bluenos-cons)
      * [Early-Stage Problems](#early-stage-problems)
         * [Problem: Setting up New VMs](#problem-setting-up-new-vms)
            * [Solution: Docker](#solution-docker)
         * [Problem: Sharing Data with Team Members](#problem-sharing-data-with-team-members)
            * [Solution: NFS](#solution-nfs)
         * [Problem: Understanding Your Data](#problem-understanding-your-data)
            * [Solution 1: Plotting (with Blueno)](#solution-1-plotting-with-blueno)
            * [Solution 2: Storing Metadata (in a Database)](#solution-2-storing-metadata-in-a-database)
      * [Mid-Stage Problems](#mid-stage-problems)
         * [Problem: Coordinating with Other Members](#problem-coordinating-with-other-members)
            * [Solution: Experiment Tracking](#solution-experiment-tracking)
         * [Problem: Controlling Cloud Costs](#problem-controlling-cloud-costs)
            * [Solution: Kubernetes](#solution-kubernetes)
         * [Problem: Running Enough Batch Jobs](#problem-running-enough-batch-jobs)
            * [Solution: Kubernetes Jobs](#solution-kubernetes-jobs)
         * [Problem: Installing or Developing ML Tools](#problem-installing-or-developing-ml-tools)
            * [Solution: Kubernetes](#solution-kubernetes-1)
         * [Problem: Handling New Training Data](#problem-handling-new-training-data)
            * [Solution: Kubernetes (Cron)Jobs](#solution-kubernetes-cronjobs)
      * [Late-Stage Problems](#late-stage-problems)
         * [Problem: Remembering Past Approaches](#problem-remembering-past-approaches)
            * [Solution: Experiment Tracking](#solution-experiment-tracking-1)
         * [Problem: Working Between Multiple CUDA/Tensorflow Versions](#problem-working-between-multiple-cudatensorflow-versions)
            * [Solution: Docker](#solution-docker-1)
         * [Problem: Migrating Away from the Cloud](#problem-migrating-away-from-the-cloud)
            * [Solutions: Kubernetes and NFS](#solutions-kubernetes-and-nfs)
         * [Problem: Model Deployment](#problem-model-deployment)
            * [Solution: Kubernetes](#solution-kubernetes-2)
         * [Problem: Onboarding New Members](#problem-onboarding-new-members)
            * [Solution: Blueno UI, Experiment Tracking UI](#solution-blueno-ui-experiment-tracking-ui)

### Assumptions
1. You are working for 1-3 months on an image dataset.
2. You are working with 2-5 other technical members.
    - If you are working solo only some of the points will apply. 
3. You do not have an infrastructure team that can solve your problems within 1-2 days.
4. You have decided that working on the public cloud sounds appealing.
    - You may have received cloud credits.
5. Your team is inexperienced. Also, your team is more familiar with algorithms than with systems.
    - If you already use Ansible or similar solutions, then you probably have a good idea of how to evolve your ML infrastructure over time and won’t necessarily need this tool.

### Blueno's Cons
It's fair to consider whether this is the right tool for you. Here are some issues we've try to address.

- Blueno is a tool that you would need to learn.
    - We try to make it easy to learn by keeping the user interface small. We only expose non-configurable setup scripts, a 9-method Python client, and a minimal web UI. Still, this would take at least an hour to get really familiar with.
- Blueno takes 30-60 minutes to get fully started with.
- __Blueno assumes that you will use the Kubernetes CLI frequently__
    - This means that you will need to learn how to use Kubernetes. If you aren’t familiar with the DevOps scene, this is about as difficult as learning your first programming language.
    - Given how many up-and-coming ML tools are using Docker and Kubernetes, we believe that it would be worth the cost to become familiar with them.
- Blueno will break. This is a new tool and we only test common cases. See the testing status for more info on what has been tested.
    - We try to keep things simple and provide you with documentation in the source code to help you fix the issues that you encounter.
- __We assume that the project will not last.__ This project tries to funnel you to more ambitious projects and force you to face problems with your ML infrastructure early on.
## Early-Stage Problems
Problems that will dominate your time during the first few weeks of the project.
### Problem: Setting up New VMs

If you are using cloud compute, you would need to configure GPU drivers and install Python dependencies before being able to work.
This takes 30-120 minutes to do the first time around and would take at least 15 minutes to do every time you want to use a new VM.

#### Solution 1: Solutions provided by your CSP (AMIs) 
EC2 AMIs, for example, will come with the necessary software installed.

#### Solution 2: Docker on Kubernetes
Docker images also can provide similar functionality to AMIs. One issue is that
you need to manually set up Docker a new instance.
With Kubernetes, it becomes easier because you can simply specify the image tag
in a configuration file to get things working.

### Problem: Sharing Data with Team Members
####  Solution: NFS
While NFS is not always the greatest option (esp. on top of Kubernetes), it makes more sense to use as the default over the 2 most common alternatives: disk storage and object storage.

The issue with disk storage is that, generally, you can only attach a disk to one VM. This means that if you want to run more GPU training jobs than the number of GPUs your instance has, you need to manually work around the problem. It takes at 5-15 minutes to produce snapshots of these disks and then spin up additional instances. Finally, you end up with reproducibility issues too quickly unless your team members coordinate well. Over the course of even 1 month, the problems will rack up.

Object storage (S3, etc.), like NFS, takes less time and effort to manage than disk. However, it's generally too slow since you need to pull the data to your instance to train a model. Also, you may not be able to use a lot of convenience methods which assumes that your data is mounted on the filesystem. If you decide to work around this issue by downloading to disk, you end up with similar management issues that with the disk-only approach.

NFS is not a silver bullet but it allows you to simply keep your data in one place while still supporting good-enough performance for training ML. It has less prominent issues that disk and object storage so using it by default often makes sense. 
### Problem: Understanding Your Data
#### Solution 1: Plotting (with Blueno)
It helps to know what your data looks like before you train a model. If you do heavy preprocessing, plotting your data is a good way to catch bugs early on.

Blueno automatically generates images of your 2D or 3D data when you upload it through the Python client. Our team worked with CT scans and 10% of our accuracy increase could be attributed to repeatedly experimenting with our 3D-to-2D preprocessing pipeline.
#### Solution 2: Storing Metadata (in a Database)
Knowing the shape, labels, and previous preprocessing applied to the data helps. The most common way to do so is to use a CSV or JSON file.

We put that data in a relational database instead. This has many benefits:
- We can easily display the data on the web UI.
- Adding additional training data in the future becomes simpler.
- You can use SQL analytics tools to drill down on your metadata.
 It’s easier for you to build your own cronjobs and applications on the data.

There are clear performance limitations with this approach, but for most datasets it is fine.


## Mid-Stage Problems
At this point, you’ve got everything set up. Your team has trained a few models and understands the data. Your biggest problem at this point is quickly building a good deep learning model.
### Problem: Coordinating with Other Members
#### Solution: Experiment Tracking
If you are working with others, you may want to avoid working on the same things too often. You can avoid this by using an experiment tracking tool.

After running a training job, you would upload your results with code similar to the following:
```
mlflow.log_param(‘architecture’, ‘resnet’)
mlflow.log_param(‘author’, ‘luke’)
mlflow.log_metric(‘val_acc’, 0.7533)
```
Since everybody can quickly see and filter results on the web dashboard, it becomes a lot easier to coordinate.
### Problem: Controlling Cloud Costs
#### Solution: Kubernetes (Cluster Autoscaler and Scheduler)
For deep learning projects, GPUs are the largest source of cloud costs and you generally don’t want to be using them unless you need to. Leaving a GPU instance idle for a few nights costs hundreds of dollars.

A Kubernetes cluster with cluster autoscaling enabled will downscale an idle GPU instance after ~10 minutes. Especially if you are running training jobs overnight, this can be very useful at reducing costs.

In addition, CPUs and memory can still cost a few hundred dollars over a month. Kubernetes schedules your programs on the same node if possible, saving you a bit over time.
### Problem: Running Enough Batch Jobs
#### Solution: Kubernetes Jobs
One of the best ways to increase productivity is to run preprocessing and training jobs in the background. Anecdotally, many people don’t end up running enough jobs in the background because of the complexity. Setting up training and preprocessing jobs with Kubernetes becomes a 5-10 minute process requiring 5 `kubectl` commands. As a result, this leads to teams that are limited by the number of ideas they want to try out rather than the number of Jupyter notebooks they can keep open.

Here is what the process typically looks like without a configuration management tool:
1. Estimate how much memory and disk space the job needs.
    - If running the job overnight, alter the code so that the instance running the job is not idle for too long overnight.
2. If needed, spin up a VM of the right type. Wait 5-10 minutes for it to be ready.
3. If creating a new disk snapshot, wait an additional 5-10 minutes.
4. SSH into your machine and do some more manual setup (`git checkout`, updating Python requirements, copying secret files, etc.), if necessary.
5. Start the job and check its logs to make sure things are working.
    - Fix any bugs and copy over the changes with several `git` commands or with `scp`.
    - Periodically SSH in and check the logs all created jobs with SSH. When done, delete unneeded VMs and snapshots.

With Kubernetes, the process would look like this:
1. Push up a Docker image with the code you want to run.
    - If using an altered requirements.txt file, wait ~5 minutes for the image to be pushed up. If not, wait for ~10 seconds.
2. Estimate how much memory and disk space the job needs.
3. Write up a Kubernetes Job configuration file. Over the first couple of days, this would take 15-30 minutes. After a while, it takes less than 2 minutes to do.
4. Submit the Kubernetes job with `kubectl apply -f <config-yaml>`. The job will start in ~5 minutes if a new node is needed. Otherwise, it will start in less than a minute.
5. Verify that the job is working using `kubectl describe …` and `kubectl logs …`.
    - Fix any bugs, push up the image, and resubmit the job.
    - Periodically check the logs all created jobs using `kubectl`.

The Kubernetes approach quickly becomes a straightforward 5-10 minute process that requires 3-5 commands. The first approach can also take 5-10 minutes if done properly but usually takes 20-30. It also requires 10+ commands and more knowledge of Unix to do things correctly, which stops a lot of people from submitting such jobs even if they want to.
### Problem: Installing or Developing ML Tools
#### Solution: Kubernetes
If you want to set up and share tools like Tensorboard, Airflow, or [Quiver](https://github.com/keplr-io/quiver), Kubernetes simplifies the process of bringing up those tools. Since it still takes 30 minutes to a couple of hours to set up such tools, it’s not necessarily worth it for all users, but it’s a good option to have.

Kubernetes also simplifies development. For example, our group wanted a data annotation tool for annotating medical image data. This would allow us to try building object detection models in addition to classification ones.
I ended up spending ~2 work-days to write a simple one and ended up deploying to Google App Engine so that radiologists could help annotate the data.
Deploying to Kubernetes would have been as simple and more cost-effective for us.
If you have the need to build similar applications as well for your dataset, K8s would simplify things greatly.

### Problem: Handling New Training Data
#### Solution: Kubernetes (Cron)Jobs
If you are consistently fetching additional training data and labels, having a re-runnable data pipeline can be helpful. Kubernetes makes it easy to write reproducible programs and run your jobs on a certain schedule.

## Late-Stage Problems
At this point, you’ve been working for a couple months. You may be wrapping up your project or attempting to do more challenging things with your data.
### Problem: Remembering Past Approaches
#### Solution: Experiment Tracking
At some point, you will start to forget what you’ve tried out. An experimenting tracking dashboard allows you to quickly query and see what was done.
### Problem: Working Between Multiple CUDA/Tensorflow Versions
#### Solution: Docker
At any moment in time, there will be at least 2 major CUDA versions in use. At the moment, CUDA 9 and CUDA 10 are popular. My university still runs CUDA 8.

For a short project, it’s usually better to avoid upgrading such dependencies until you want to use a certain feature. Using Docker image which specifies a CUDA version can help you avoid wasting time managing incompatibility issues.
### Problem: Migrating Away from the Cloud
#### Solutions: Kubernetes and NFS
After a few months, you may decide to purchase your own machine for doing deep learning or move to another cloud platform.
Given that cloud GPU costs are fairly high, the migration back worth considering. 

While not easy, stayin on K8s and NFS is far simpler figuring out how to migrate data in cloud object storage or figuring out how to work without certain CSP-specific features.
### Problem: Model Deployment
#### Solution: Kubernetes
If you are deploying a model, this amount of infrastructure may still not be enough. I don’t have too much experience in this area, but there are many steps like retraining models and monitoring model performance that require extra infrastructure to support.

If you are doing this step, having a Kubernetes cluster can simplify the issue, especially since a lot of the tools in the ecosystem that target this step run on Docker or Kubernetes.
### Problem: Onboarding New Members
#### Solution: Blueno UI, Experiment Tracking UI
Over the course of 1-3 months, your code will grow complicated, especially if you are rightfully focusing on getting a decently-performing model.

Having images of the data and charts of what has been already data will help immensely with getting others up-to-speed.

Also, at that point, it’s likely easier for new members to learn how to work with Docker and Kubernetes than it is for them to navigate through your code and your data.
