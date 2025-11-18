import mitt from 'mitt';

type Events = {
  refreshUserImages: any;
  openPosterGenerate: void;
  closePosterGenerate: void;
};

const emitter = mitt<Events>();

export default emitter;
