const { getCompositions, renderMedia } = require('@remotion/renderer');
const { bundle } = require('@remotion/bundler');
const path = require('path');

const renderVideo = async () => {
  try {
    console.log('Bundling the Remotion project...');
    const bundleLocation = "http://localhost:3000" //await bundle(path.resolve('./src/index.ts')); // Adjust the entry file if necessary
    console.log(`Bundle created at: ${bundleLocation}`);

    console.log('Fetching compositions from the bundle...');
    const compositions = await getCompositions(bundleLocation);
    if (!compositions || compositions.length === 0) {
      throw new Error('No compositions found in the bundle.');
    }
    console.log('Available compositions:', compositions);

    const composition = compositions.find((comp) => comp.id === 'CaptionedVideo');
    if (!composition) {
      throw new Error('Composition "CaptionedVideo" not found.');
    }

    console.log('Composition details:', composition);

    // Validate dimensions
    if (!composition.width || !composition.height) {
      throw new Error('Invalid composition dimensions.');
    }
    if (composition.width % 2 !== 0 || composition.height % 2 !== 0) {
      throw new Error(
        `Composition dimensions must be even. Found: width=${composition.width}, height=${composition.height}`
      );
    }

    console.log('Rendering video...');
    const outputLocation = path.join(__dirname, 'out', 'video.mp4');

    await renderMedia({
      composition: 'CaptionedVideo',
      serveUrl: "http://localhost:3000",
      codec: 'h264',
      outputLocation,
      width: composition.width, // Use dimensions from the composition
      height: composition.height,
    });

    console.log(`Video rendered successfully to ${outputLocation}`);
  } catch (error) {
    console.error('Error during rendering:', error.message);
  }
};

renderVideo();