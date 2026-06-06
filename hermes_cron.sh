#!/bin/bash
# Hermes agent cron script: every 5 minutes, send a prompt to both Hermes sessions (Kimi K2.5 and Nemotron 3 Super)
# Prompt: "hermes ,you do not leep you are working with Rehoboam on the telegram and fetch from the web searching costumers on telegram group ,we have one week free web3 signale,make sure you deliver quality content and accurate predicrtions"

PROMPT="hermes ,you do not leep you are working with Rehoboam on the telegram and fetch from the web searching costumers on telegram group ,we have one week free web3 signale,make sure you deliver quality content and accurate predicrtions"

# Broadcast prompt to all open pseudo-terminals (pts)
for TTY in /dev/pts/[0-9]*; do
  if [ -w "$TTY" ]; then
    echo "$PROMPT" > "$TTY"
  fi
done

# Optionally, notify agent manager (customize as needed)
# echo "$PROMPT" | nc localhost 7654  # Example: send to agent manager socket

# Log action (optional)
echo "[$(date)] Prompt broadcast to all open terminals" >> /var/log/hermes_cron.log
