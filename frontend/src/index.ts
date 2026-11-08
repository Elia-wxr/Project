import { JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';

import { TarotClient } from './api';
import { TarotSidebar } from './sidebar';

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'tarot-jupyterlab:sidebar',
  autoStart: true,
  activate(app: JupyterFrontEnd) {
    const client = new TarotClient(app.serviceManager.serverSettings);
    const sidebar = new TarotSidebar(client);
    app.shell.add(sidebar, 'left', { rank: 900 });
    void sidebar.checkConnection();
  }
};

export default plugin;
