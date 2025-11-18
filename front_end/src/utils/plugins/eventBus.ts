import mitt from 'mitt';

type Events = {
  refreshUserImages: any;
  openPosterGenerate: void;
};

const emitter = mitt<Events>();

export default emitter;
