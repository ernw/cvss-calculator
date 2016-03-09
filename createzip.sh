#!/bin/sh
cd "$(dirname "$0")"
zip cvsscalc.zip __main__.py cvsscalc/*.py cvsscalc/tooltips/*/* cvsscalc/cvsscalc.ico cvsscalc/*.xrc

echo '#!/usr/bin/env python2' > cvsscalc.zippy
cat cvsscalc.zip >> cvsscalc.zippy
rm -f cvsscalc.zip
chmod 755 cvsscalc.zippy
