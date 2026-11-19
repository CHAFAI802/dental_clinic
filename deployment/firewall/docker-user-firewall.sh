#!/bin/sh
set -eu

IPT="/usr/sbin/iptables"
CHAIN="DOCKER-USER"
PUBLIC_IP="179.67.198.151"

# 1. Supprimer les anciennes règles HTTP/HTTPS trop générales.
for PORT in 80 443; do
    while $IPT -w 10 -C "$CHAIN" \
        -i eth0 -p tcp \
        -m conntrack --ctorigdstport "$PORT" \
        -j RETURN 2>/dev/null; do

        $IPT -w 10 -D "$CHAIN" \
            -i eth0 -p tcp \
            -m conntrack --ctorigdstport "$PORT" \
            -j RETURN
    done
done

# 2. Nettoyer les anciennes règles de connexions établies.
while $IPT -w 10 -C "$CHAIN" \
    -i eth0 \
    -m conntrack --ctstate ESTABLISHED,RELATED \
    -j RETURN 2>/dev/null; do

    $IPT -w 10 -D "$CHAIN" \
        -i eth0 \
        -m conntrack --ctstate ESTABLISHED,RELATED \
        -j RETURN
done

# 3. Supprimer les règles HTTP/HTTPS ciblant les anciennes
# et les nouvelles adresses de Caddy.
for TARGET_IP in 172.20.0.2 172.21.0.4; do
    for PORT in 80 443; do
        while $IPT -w 10 -C "$CHAIN" \
            -i eth0 -p tcp -d "$TARGET_IP" \
            -m conntrack --ctorigdstport "$PORT" \
            -j RETURN 2>/dev/null; do

            $IPT -w 10 -D "$CHAIN" \
                -i eth0 -p tcp -d "$TARGET_IP" \
                -m conntrack --ctorigdstport "$PORT" \
                -j RETURN
        done
    done
done

# 4. Supprimer les anciennes règles DROP gérées par ce script.
while $IPT -w 10 -C "$CHAIN" -i eth0 -j DROP 2>/dev/null; do
    $IPT -w 10 -D "$CHAIN" -i eth0 -j DROP
done

# 5. Autoriser les réponses aux connexions initiées par les conteneurs.
$IPT -w 10 -I "$CHAIN" 1 \
    -i eth0 \
    -m conntrack --ctstate ESTABLISHED,RELATED \
    -j RETURN

# 6. Autoriser HTTP uniquement vers Caddy.
$IPT -w 10 -I "$CHAIN" 2 \
    -i eth0 -p tcp \
    -m conntrack --ctorigdst "$PUBLIC_IP" --ctorigdstport 80 \
    -j RETURN

# 7. Autoriser HTTPS uniquement vers Caddy.
$IPT -w 10 -I "$CHAIN" 3 \
    -i eth0 -p tcp \
    -m conntrack --ctorigdst "$PUBLIC_IP" --ctorigdstport 443 \
    -j RETURN

# 8. Bloquer les autres connexions entrantes vers les conteneurs.
$IPT -w 10 -A "$CHAIN" -i eth0 -j DROP

echo "Docker IPv4 firewall rules applied."
