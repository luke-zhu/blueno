export const DATASETS = [
  // 'abstract_reasoning', // Requires 'apache_beam' to be installed
  // 'caltech101', // Labels are not available, TFDS bug
  'cats_vs_dogs',
  'celeb_a',
  'cifar10',
  'cifar10_corrupted',
  'cifar100',
  'coco2014',
  'colorectal_histology',
  'colorectal_histology_large',
  'cycle_gan',
  // 'diabetic_retinopathy_detection', // Requires manual download
  // 'dsprites', // eviction issue
  // 'dtd', // Labels not available
  'horses_or_humans',
  // 'imagenet2012', // don't support this, way too slow
  // 'imagenet2012_corrupted', // untested
  'kmnist',
  // 'lsun', // too large for now
  'mnist',
  'omniglot',
  // 'open_images_v4', // too large for now, also check out v5
  'oxford_flowers102',
  'oxford_iiit_pet',
  // 'quickdraw_bitmap', // too large for now, resize first
  'rock_paper_scissors',
  'shapes3d', // eviction issue
  'smallnorb',
  // "sun397", // Labels not avaialble,
  "svhn_cropped",
  'tf_flowers',
  "voc2007",
  // TODO: add video datasets if possible
];