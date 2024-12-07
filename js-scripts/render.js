// render.js
const { renderMedia } = require('@remotion/renderer');
const path = require('path');

const renderVideo = async () => {
  const compositionId = 'CaptionedVideo';
  // eslint-disable-next-line no-undef
  const outputLocation = path.join(__dirname, 'out', 'video.mp4');

  await renderMedia({
    composition: compositionId,
    serveUrl: 'http://localhost:3000',
    codec: 'h264',
    outputLocation,
  });

  console.log(`Video rendered to ${outputLocation}`);
};

renderVideo().catch((err) => {
  console.error(err);
});