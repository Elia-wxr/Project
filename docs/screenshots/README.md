# Sidebar screenshots (task A evidence)

Captured from the real extension running inside JupyterLab 4.6.6 (not a mock
page), at `deviceScaleFactor=2`.

| File | Content |
| --- | --- |
| `a-sidebar-light-480.png` | Light theme, 480 px sidebar, Demo reading, `Unsaved`. |
| `a-sidebar-light-320.png` | Light theme, 320 px sidebar, wrapping instead of overflow. |
| `a-sidebar-dark-480.png` | Dark theme, 480 px. |
| `a-sidebar-dark-320.png` | Dark theme, 320 px. |
| `a-settings-light-480.png` | Light theme AI settings tab (task B-01 panel, mounted by A). |
| `a-settings-dark-480.png` | Dark theme AI settings tab. |
| `a-jupyterlab-dark-480.png` | Whole JupyterLab window, dark theme. |
| `a-sidebar-focus-480.png` | Keyboard focus ring on `Save as latest` after Tab. |

The 320 px and 480 px captures use the real splitter; `scrollWidth` equals
`clientWidth` in both, so there is no horizontal overflow. The tab in the left
activity bar is addressable as role `tab` with the accessible name `Tarot`.

Known issue outside this task: the radio group in the AI settings panel lays
out its inputs oddly (B-01 owns `settings.css`); report it to B rather than
patching it here.
