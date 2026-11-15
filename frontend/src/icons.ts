import { LabIcon } from '@jupyterlab/ui-components';

import tarotSvg from '../style/icons/tarot.svg';

/**
 * Single-color icon for the left activity bar: a card with a centred diamond.
 * The SVG only uses `currentColor`/`jp-icon3`, so it follows the active theme.
 */
export const tarotIcon = new LabIcon({
  name: 'tarot-jupyterlab:tarot',
  svgstr: tarotSvg
});
