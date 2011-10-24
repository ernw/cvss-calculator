#!/bin/sh

rm -f cvsscalc.zip
zip cvsscalc.zip __main__.py cvsscalc/*.py

echo '#!/usr/bin/env python2' > cvsscalc.zippy
cat cvsscalc.zip >> cvsscalc.zippy
chmod 755 cvsscalc.zippy
