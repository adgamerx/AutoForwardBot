echo "Cloning Repo...."
if [ -z $BRANCH ]
then
  echo "Cloning main branch...."
  git clone https://github.com/ADx/ADx-AutoForward-Bot ADx/ADx-AutoForward-Bot
else
  echo "Cloning $BRANCH branch...."
  git clone https://github.com/ADx/ADx-AutoForward-Bot -b $BRANCH /ADx-AutoForward-Bot
fi
cd ADx/ADx-AutoForward-Bot
pip3 install -U -r requirements.txt
echo "Starting Bot...."
gunicorn app:app & python3 main.py
