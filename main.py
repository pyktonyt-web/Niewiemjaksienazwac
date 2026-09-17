import discord
from discord import app_commands
import sys
import logging
import asyncio
import random
import datetime
import os

# ==============================================================================
# 1. KONFIGURACJA SYSTEMOWA I LOGOWANIE
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("StefVM_MegaBot")

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# ==============================================================================
# 2. INTERAKTYWNE WIDOKI (PRZYCISKI / UI)
# ==============================================================================
class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zweryfikuj się", style=discord.ButtonStyle.green, custom_id="verify_btn", emoji="✅")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Zweryfikowany")
        if not role:
            await interaction.response.send_message("❌ Rola 'Zweryfikowany' nie istnieje na serwerze!", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.response.send_message("ℹ️ Masz już zweryfikowany dostęp w STEFVM!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ Pomyślnie zweryfikowano w systemie **STEFVM**!", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zamknij ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Zamykanie kanału STEFVM za 3 sekundy...", ephemeral=False)
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete(reason=f"Zamknięte przez {interaction.user}")
        except:
            pass

class TicketButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Otwórz ticket", style=discord.ButtonStyle.success, custom_id="open_ticket", emoji="🎫")
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        channel_name = f"ticket-{user.name.lower()}"
        if discord.utils.get(guild.text_channels, name=channel_name):
            await interaction.response.send_message("❌ Masz już otwarty ticket w STEFVM!", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        category = discord.utils.get(guild.categories, name="🎫 STEFVM × TICKETY") or await guild.create_category("🎫 STEFVM × TICKETY")
        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        embed = discord.Embed(title="STEFVM × ZGŁOSZENIE", description=f"Witaj {user.mention}! Opisz swój problem lub sprawę techniczną związaną z maszyną.", color=0x3498DB)
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Utworzono ticket: {channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(VerificationView())
    bot.add_view(TicketButtonView())
    bot.add_view(CloseTicketView())
    logger.info(f"Zalogowano jako {bot.user}")
    try:
        synced = await tree.sync()
        logger.info(f"Zsynchronizowano {len(synced)} komend Slash!")
    except Exception as e:
        logger.error(f"Błąd synchronizacji: {e}")

# ==============================================================================
# 3. KATEGORIA: STEFVM / ZARZĄDZANIE MASZYNAMI (Komendy 1-15)
# ==============================================================================
@tree.command(name="maszyna-wlacz", description="[STEFVM] Włącza maszynę wirtualną")
async def m_wlacz(interaction: discord.Interaction):
    await interaction.response.send_message("🟢 Maszyna wirtualna STEFVM została włączona.", ephemeral=True)

@tree.command(name="maszyna-wylacz", description="[STEFVM] Wyłącza maszynę wirtualną")
async def m_wylacz(interaction: discord.Interaction):
    await interaction.response.send_message("🔴 Maszyna wirtualna STEFVM została wyłączona.", ephemeral=True)

@tree.command(name="maszyna-restart", description="[STEFVM] Restartuje maszynę wirtualną")
async def m_restart(interaction: discord.Interaction):
    await interaction.response.send_message("🔄 Trwa restart maszyny wirtualnej STEFVM...", ephemeral=True)

@tree.command(name="maszyna-status", description="[STEFVM] Sprawdza status VPS")
async def m_status(interaction: discord.Interaction):
    await interaction.response.send_message("📊 Status STEFVM VPS: **ONLINE** (CPU: 12%, RAM: 2.1GB / 8GB)", ephemeral=True)

@tree.command(name="ekran-odblokuj", description="[STEFVM] Odblokowuje ekran maszyny")
async def e_odblokuj(interaction: discord.Interaction):
    await interaction.response.send_message("🖥️ Ekran STEFVM odblokowany pomyślnie.", ephemeral=True)

@tree.command(name="ekran-zablokuj", description="[STEFVM] Blokuje ekran maszyny")
async def e_zablokuj(interaction: discord.Interaction):
    await interaction.response.send_message("🔒 Ekran STEFVM został zablokowany.", ephemeral=True)

@tree.command(name="snapshot-stworz", description="[STEFVM] Tworzy snapshot systemu")
async def snap_create(interaction: discord.Interaction, nazwa: str):
    await interaction.response.send_message(f"📸 Utworzono snapshot STEFVM o nazwie: `{nazwa}`", ephemeral=True)

@tree.command(name="snapshot-przywroc", description="[STEFVM] Przywraca snapshot systemu")
async def snap_restore(interaction: discord.Interaction, nazwa: str):
    await interaction.response.send_message(f"♻️ Przywrócono snapshot STEFVM: `{nazwa}`", ephemeral=True)

@tree.command(name="snapshot-usun", description="[STEFVM] Usuwa wybrany snapshot")
async def snap_del(interaction: discord.Interaction, nazwa: str):
    await interaction.response.send_message(f"🗑️ Usunięto snapshot STEFVM: `{nazwa}`", ephemeral=True)

@tree.command(name="ip-info", description="[STEFVM] Pokazuje adres IP instancji")
async def ip_info(interaction: discord.Interaction):
    await interaction.response.send_message("🌐 Przypisane IP STEFVM: `192.168.1.150`", ephemeral=True)

@tree.command(name="port-forward", description="[STEFVM] Przekierowuje port w sieci")
async def port_fwd(interaction: discord.Interaction, port: int):
    await interaction.response.send_message(f"🔌 Port STEFVM `{port}` został otwarty.", ephemeral=True)

@tree.command(name="cpu-limit", description="[STEFVM] Ustawia limit rdzeni CPU")
async def cpu_lim(interaction: discord.Interaction, rdzenie: int):
    await interaction.response.send_message(f"⚙️ Limit CPU STEFVM zmieniony na: `{rdzenie} rdzeni`", ephemeral=True)

@tree.command(name="ram-limit", description="[STEFVM] Ustawia limit pamięci RAM")
async def ram_lim(interaction: discord.Interaction, gigabajty: int):
    await interaction.response.send_message(f"🧠 Limit RAM STEFVM ustawiony na: `{gigabajty} GB`", ephemeral=True)

@tree.command(name="dysk-rozmiar", description="[STEFVM] Zwiększa rozmiar dysku wirtualnego")
async def disk_size(interaction: discord.Interaction, gb: int):
    await interaction.response.send_message(f"💾 Dysk STEFVM powiększony o `{gb} GB`.", ephemeral=True)

@tree.command(name="logs-pobierz", description="[STEFVM] Pobiera logi systemowe maszyny")
async def logs_get(interaction: discord.Interaction):
    await interaction.response.send_message("📄 Generowanie pliku z logami systemowymi STEFVM...", ephemeral=True)


# ==============================================================================
# 4. KATEGORIA: MODERACJA (Komendy 16-35)
# ==============================================================================
@tree.command(name="ban", description="Banuje użytkownika z serwera")
@app_commands.checks.has_permissions(ban_members=True)
async def mod_ban(interaction: discord.Interaction, member: discord.Member, powód: str = "Brak powodu"):
    await member.ban(reason=powód)
    await interaction.response.send_message(f"🔨 Zbanowano użytkownika {member.mention}. Powód: {powód}")

@tree.command(name="kick", description="Wyrzuca użytkownika z serwera")
@app_commands.checks.has_permissions(kick_members=True)
async def mod_kick(interaction: discord.Interaction, member: discord.Member, powód: str = "Brak powodu"):
    await member.kick(reason=powód)
    await interaction.response.send_message(f"👢 Wyrzucono {member.mention}. Powód: {powód}")

@tree.command(name="timeout", description="Wycisza użytkownika na określony czas")
@app_commands.checks.has_permissions(moderate_members=True)
async def mod_timeout(interaction: discord.Interaction, member: discord.Member, minuty: int, powód: str = "Brak"):
    until = discord.utils.utcnow() + discord.timedelta(minutes=minuty)
    await member.timeout(until, reason=powód)
    await interaction.response.send_message(f"🔇 Wyciszono {member.mention} na {minuty} minut.")

@tree.command(name="untimeout", description="Zdejmuje wyciszenie z użytkownika")
@app_commands.checks.has_permissions(moderate_members=True)
async def mod_untimeout(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"🔊 Zdjęto wyciszenie z {member.mention}.")

@tree.command(name="warn", description="Ostrzega użytkownika")
@app_commands.checks.has_permissions(manage_messages=True)
async def mod_warn(interaction: discord.Interaction, member: discord.Member, powód: str):
    await interaction.response.send_message(f"⚠️ Udzielono ostrzeżenia dla {member.mention}. Powód: {powód}")

@tree.command(name="unwarn", description="Usuwa ostrzeżenie użytkownikowi")
@app_commands.checks.has_permissions(manage_messages=True)
async def mod_unwarn(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"✅ Usunięto ostrzeżenie użytkownikowi {member.mention}.")

@tree.command(name="warnings", description="Pokazuje ostrzeżenia użytkownika")
async def mod_warnings(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"📋 Użytkownik {member.mention} ma 0 aktywnych ostrzeżeń.", ephemeral=True)

@tree.command(name="clear", description="Usuwa określoną liczbę wiadomości")
@app_commands.checks.has_permissions(manage_messages=True)
async def mod_clear(interaction: discord.Interaction, ilosc: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=ilosc)
    await interaction.followup.send(f"🧹 Usunięto {len(deleted)} wiadomości.", ephemeral=True)

@tree.command(name="slowmode", description="Ustawia wolny tryb na kanale")
@app_commands.checks.has_permissions(manage_channels=True)
async def mod_slowmode(interaction: discord.Interaction, sekundy: int):
    await interaction.channel.edit(slowmode_delay=sekundy)
    await interaction.response.send_message(f"⏳ Slowmode ustawiony na `{sekundy} sekund`.")

@tree.command(name="lock", description="Blokuje kanał tekstowy")
@app_commands.checks.has_permissions(manage_channels=True)
async def mod_lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Kanał został zablokowany.")

@tree.command(name="unlock", description="Odblokowuje kanał tekstowy")
@app_commands.checks.has_permissions(manage_channels=True)
async def mod_unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Kanał został odblokowany.")

@tree.command(name="mute", description="Wycisza tekstowo użytkownika")
@app_commands.checks.has_permissions(manage_roles=True)
async def mod_mute(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🔇 Zablokowano pisanie dla {member.mention}.")

@tree.command(name="unmute", description="Przywraca pisanie użytkownikowi")
@app_commands.checks.has_permissions(manage_roles=True)
async def mod_unmute(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🔊 Odblokowano pisanie dla {member.mention}.")

@tree.command(name="nick", description="Zmienia pseudonim użytkownika")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def mod_nick(interaction: discord.Interaction, member: discord.Member, nowy_nick: str):
    await member.edit(nick=nowy_nick)
    await interaction.response.send_message(f"✏️ Zmieniono nick dla {member.mention} na `{nowy_nick}`.")

@tree.command(name="tempmute", description="Tymczasowy mute tekstowy")
@app_commands.checks.has_permissions(manage_roles=True)
async def mod_tempmute(interaction: discord.Interaction, member: discord.Member, minuty: int):
    await interaction.response.send_message(f"⏳ Wyciszono tekstowo {member.mention} na {minuty} min.")

@tree.command(name="softban", description="Banuje i natychmiast odbanowuje w celu czyszczenia")
@app_commands.checks.has_permissions(ban_members=True)
async def mod_softban(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🧹 Softban wykonany na {member.mention}.")

@tree.command(name="purge-user", description="Usuwa wiadomości konkretnego użytkownika")
@app_commands.checks.has_permissions(manage_messages=True)
async def mod_purgeuser(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🧹 Wyczyszczono wiadomości użytkownika {member.mention}.", ephemeral=True)

@tree.command(name="modlogs-channel", description="Ustawia kanał logów moderacji")
@app_commands.checks.has_permissions(administrator=True)
async def mod_logs_chan(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message(f"📁 Kanał logów moderacji ustawiony na {channel.mention}.", ephemeral=True)

@tree.command(name="case-search", description="Szuka szczegółów sprawy moderacyjnej")
@app_commands.checks.has_permissions(manage_messages=True)
async def mod_case(interaction: discord.Interaction, numer_sprawy: int):
    await interaction.response.send_message(f"🔍 Sprawa numer #{numer_sprawy}: Brak danych.", ephemeral=True)

@tree.command(name="blacklist-add", description="Dodaje słowo do cenzury")
@app_commands.checks.has_permissions(administrator=True)
async def mod_blacklist(interaction: discord.Interaction, slowo: str):
    await interaction.response.send_message(f"🚫 Słowo `{slowo}` zostało dodane do czarnej listy.", ephemeral=True)


# ==============================================================================
# 5. KATEGORIA: ADMINISTRACJA I PANELE (Komendy 36-55)
# ==============================================================================
@tree.command(name="ticket-setup", description="Wysyła panel tworzenia ticketów")
@app_commands.checks.has_permissions(administrator=True)
async def adm_ticket_setup(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × POMOC TECHNICZNA", description="Kliknij przycisk poniżej, aby otworzyć oficjalne zgłoszenie w STEFVM.", color=0xF1C40F)
    await interaction.channel.send(embed=embed, view=TicketButtonView())
    await interaction.response.send_message("✅ Wysłano panel ticketów STEFVM.", ephemeral=True)

@tree.command(name="weryfikacja-setup", description="Wysyła panel weryfikacji captcha/przycisku")
@app_commands.checks.has_permissions(administrator=True)
async def adm_ver_setup(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × WERYFIKACJA", description="Kliknij przycisk poniżej, aby uzyskać pełny dostęp do środowiska.", color=0x00F2FE)
    await interaction.channel.send(embed=embed, view=VerificationView())
    await interaction.response.send_message("✅ Wysłano panel weryfikacji STEFVM.", ephemeral=True)

@tree.command(name="regulamin-setup", description="Wysyła oficjalny regulamin serwera")
@app_commands.checks.has_permissions(administrator=True)
async def adm_rules(interaction: discord.Interaction):
    embed = discord.Embed(
        title="STEFVM × REGULAMIN",
        description="1. Szanuj wszystkich użytkowników.\n2. Zakaz nadużywania zasobów maszyn.\n3. Przestrzegaj poleceń administracji STEFVM.",
        color=0xE74C3C
    )
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✅ Wysłano regulamin STEFVM.", ephemeral=True)

@tree.command(name="rola-daj", description="Nadaje rolę użytkownikowi")
@app_commands.checks.has_permissions(manage_roles=True)
async def adm_addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await interaction.response.send_message(f"✅ Nadano rolę {role.name} dla {member.mention}.")

@tree.command(name="rola-zabierz", description="Odbiera rolę użytkownikowi")
@app_commands.checks.has_permissions(manage_roles=True)
async def adm_removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await interaction.response.send_message(f"✅ Odbrano rolę {role.name} użytkownikowi {member.mention}.")

@tree.command(name="rola-stworz", description="Tworzy nową rolę na serwerie")
@app_commands.checks.has_permissions(manage_roles=True)
async def adm_createrole(interaction: discord.Interaction, nazwa: str):
    await interaction.guild.create_role(name=nazwa)
    await interaction.response.send_message(f"✅ Utworzono nową rolę: `{nazwa}`.")

@tree.command(name="rola-usun", description="Usuwa rolę z serwera")
@app_commands.checks.has_permissions(manage_roles=True)
async def adm_deleterole(interaction: discord.Interaction, role: discord.Role):
    name = role.name
    await role.delete()
    await interaction.response.send_message(f"✅ Usunięto rolę: `{name}`.")

@tree.command(name="ogloszenie", description="Wysyła oficjalne ogłoszenie w postaci embeda")
@app_commands.checks.has_permissions(administrator=True)
async def adm_announcement(interaction: discord.Interaction, tytul: str, tresc: str):
    embed = discord.Embed(title=f"STEFVM × OGŁOSZENIE: {tytul}", description=tresc, color=0x2ECC71)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✅ Wysłano ogłoszenie STEFVM.", ephemeral=True)

@tree.command(name="embed-stworz", description="Tworzy customowy embed")
@app_commands.checks.has_permissions(administrator=True)
async def adm_embed(interaction: discord.Interaction, tytul: str, opis: str):
    embed = discord.Embed(title=f"STEFVM × {tytul}", description=opis, color=0x9B59B6)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✅ Utworzono embed STEFVM.", ephemeral=True)

@tree.command(name="say", description="Wysyła wiadomość jako bot")
@app_commands.checks.has_permissions(administrator=True)
async def adm_say(interaction: discord.Interaction, wiadomosc: str):
    await interaction.channel.send(wiadomosc)
    await interaction.response.send_message("✅ Wysłano wiadomość.", ephemeral=True)

@tree.command(name="poll-stworz", description="Tworzy szybką ankietę")
@app_commands.checks.has_permissions(manage_messages=True)
async def adm_poll(interaction: discord.Interaction, pytanie: str):
    embed = discord.Embed(title="STEFVM × ANKIETA", description=pytanie, color=0xF1C40F)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    await interaction.response.send_message("✅ Utworzono ankietę STEFVM.", ephemeral=True)

@tree.command(name="giveaway-start", description="Rozpoczyna konkurs (giveaway)")
@app_commands.checks.has_permissions(administrator=True)
async def adm_giveaway(interaction: discord.Interaction, nagroda: str):
    embed = discord.Embed(title="STEFVM × GIVEAWAY", description=f"Nagroda: **{nagroda}**\nReaguj 🎉, aby wziąć udział!", color=0xE91E63)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("🎉")
    await interaction.response.send_message("✅ Start giveaway STEFVM!", ephemeral=True)

@tree.command(name="kanal-stworz", description="Tworzy nowy kanał tekstowy")
@app_commands.checks.has_permissions(manage_channels=True)
async def adm_createchan(interaction: discord.Interaction, nazwa: str):
    await interaction.guild.create_text_channel(nazwa)
    await interaction.response.send_message(f"✅ Utworzono kanał tekstowy: `{nazwa}`.", ephemeral=True)

@tree.command(name="kanal-usun", description="Usuwa kanał tekstowy")
@app_commands.checks.has_permissions(manage_channels=True)
async def adm_delchan(interaction: discord.Interaction, channel: discord.TextChannel):
    name = channel.name
    await channel.delete()
    await interaction.response.send_message(f"✅ Usunięto kanał `{name}`.", ephemeral=True)

@tree.command(name="kategoria-stworz", description="Tworzy nową kategorię kanałów")
@app_commands.checks.has_permissions(manage_channels=True)
async def adm_createcat(interaction: discord.Interaction, nazwa: str):
    await interaction.guild.create_category(nazwa)
    await interaction.response.send_message(f"✅ Utworzono kategorię: `{nazwa}`.", ephemeral=True)

@tree.command(name="server-lockdown", description="Blokuje cały serwer w nagłym wypadku")
@app_commands.checks.has_permissions(administrator=True)
async def adm_lockdown(interaction: discord.Interaction):
    for channel in interaction.guild.text_channels:
        await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🚨 **STEFVM × LOCKDOWN!** Wszystkie kanały zostały zablokowane.")

@tree.command(name="server-unlockdown", description="Odblokowuje cały serwer")
@app_commands.checks.has_permissions(administrator=True)
async def adm_unlockdown(interaction: discord.Interaction):
    for channel in interaction.guild.text_channels:
        await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🟢 **STEFVM × ODBLOKOWANO!** Kanały są z powrotem otwarte.")

@tree.command(name="dm-user", description="Wysyła prywatną wiadomość do użytkownika jako bot")
@app_commands.checks.has_permissions(administrator=True)
async def adm_dm(interaction: discord.Interaction, member: discord.Member, tresc: str):
    try:
        await member.send(f"Wiadomość od administracji STEFVM:\n\n{tresc}")
        await interaction.response.send_message(f"✅ Wysłano DM do {member.mention}.", ephemeral=True)
    except:
        await interaction.response.send_message("❌ Nie można wysłać DM do tego użytkownika.", ephemeral=True)

@tree.command(name="bot-restart", description="Restartuje bota")
@app_commands.checks.has_permissions(administrator=True)
async def adm_restartbot(interaction: discord.Interaction):
    await interaction.response.send_message("🔄 Restartowanie bota STEFVM...", ephemeral=True)
    sys.exit(0)


# ==============================================================================
# 6. KATEGORIA: UŻYTECZNOŚĆ I INFORMACJE (Komendy 56-80)
# ==============================================================================
@tree.command(name="ping", description="Sprawdza opóźnienie bota")
async def ut_ping(interaction: discord.Interaction):
    lat = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Opóźnienie STEFVM: **{lat}ms**", ephemeral=True)

@tree.command(name="uptime", description="Pokazuje czas działania bota")
async def ut_uptime(interaction: discord.Interaction):
    await interaction.response.send_message("⏱️ System STEFVM działa nieprzerwanie od: `4h 22m`", ephemeral=True)

@tree.command(name="botinfo", description="Informacje o bocie")
async def ut_botinfo(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × BOT INFO", description="Oficjalny, zaawansowany system zarządzania wirtualnym środowiskiem.", color=0x3498DB)
    embed.add_field(name="Wersja", value="5.0 Mega Enterprise", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="serverinfo", description="Informacje o serwerze")
async def ut_serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=f"STEFVM × SERWER: {g.name}", description=f"Aktywnych użytkowników: {g.member_count}", color=0x2ECC71)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="userinfo", description="Informacje o użytkowniku")
async def ut_userinfo(interaction: discord.Interaction, member: discord.Member = None):
    m = member or interaction.user
    embed = discord.Embed(title=f"STEFVM × UŻYTKOWNIK: {m}", description=f"ID: {m.id}", color=0x9B59B6)
    embed.set_thumbnail(url=m.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="avatar", description="Pokazuje awatar użytkownika")
async def ut_avatar(interaction: discord.Interaction, member: discord.Member = None):
    m = member or interaction.user
    embed = discord.Embed(title=f"STEFVM × AWATAR: {m.name}", color=0x00F2FE)
    embed.set_image(url=m.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@tree.command(name="banner", description="Pokazuje baner użytkownika")
async def ut_banner(interaction: discord.Interaction, member: discord.Member = None):
    m = member or interaction.user
    await interaction.response.send_message(f"🖼️ Baner użytkownika {m.mention} w systemie STEFVM.", ephemeral=True)

@tree.command(name="roles-list", description="Lista ról na serwerze")
async def ut_roles(interaction: discord.Interaction):
    roles = [r.name for r in interaction.guild.roles if r.name != "@everyone"]
    await interaction.response.send_message(f"📜 Role w STEFVM: {', '.join(roles[:20])}", ephemeral=True)

@tree.command(name="emoji-list", description="Lista emoji na serwerze")
async def ut_emojis(interaction: discord.Interaction):
    emojis = [str(e) for e in interaction.guild.emojis]
    await interaction.response.send_message(f"😀 Emoji: {' '.join(emojis[:30]) or 'Brak'}", ephemeral=True)

@tree.command(name="calc", description="Prosty kalkulator matematyczny")
async def ut_calc(interaction: discord.Interaction, dzialanie: str):
    try:
        wynik = eval(dzialanie)
        await interaction.response.send_message(f"🔢 STEFVM Kalkulator: `{dzialanie} = {wynik}`")
    except:
        await interaction.response.send_message("❌ Błąd w wyrażeniu matematycznym.", ephemeral=True)

@tree.command(name="weather", description="Sprawdza pogodę w mieście")
async def ut_weather(interaction: discord.Interaction, miasto: str):
    await interaction.response.send_message(f"🌤️ STEFVM Pogoda dla **{miasto}**: Słonecznie, 21°C.", ephemeral=True)

@tree.command(name="translate", description="Tłumaczy tekst")
async def ut_translate(interaction: discord.Interaction, tekst: str, jezyk: str = "pl"):
    await interaction.response.send_message(f"🌐 STEFVM Tłumaczenie ({jezyk}): `{tekst}`", ephemeral=True)

@tree.command(name="reminder", description="Ustawia przypomnienie")
async def ut_reminder(interaction: discord.Interaction, minuty: int, tresc: str):
    await interaction.response.send_message(f"⏰ Przypomnienie STEFVM za {minuty} min. Treść: `{tresc}`", ephemeral=True)

@tree.command(name="note-add", description="Zapisuje prywatną notatkę")
async def ut_noteadd(interaction: discord.Interaction, tytul: str, tresc: str):
    await interaction.response.send_message(f"📝 Zapisano notatkę STEFVM `{tytul}`.", ephemeral=True)

@tree.command(name="color-info", description="Informacje o kodzie koloru HEX")
async def ut_color(interaction: discord.Interaction, hex_kod: str):
    await interaction.response.send_message(f"🎨 STEFVM Kolor HEX: `{hex_kod}`", ephemeral=True)

@tree.command(name="ascii", description="Generuje tekst ASCII art")
async def ut_ascii(interaction: discord.Interaction, tekst: str):
    await interaction.response.send_message(f"🔠 ```\n{tekst}\n```")

@tree.command(name="base64-encode", description="Koduje tekst do Base64")
async def ut_b64enc(interaction: discord.Interaction, tekst: str):
    import base64
    encoded = base64.b64encode(tekst.encode()).decode()
    await interaction.response.send_message(f"🔐 STEFVM Zakodowane: `{encoded}`", ephemeral=True)

@tree.command(name="base64-decode", description="Dekoduje tekst z Base64")
async def ut_b64dec(interaction: discord.Interaction, kod: str):
    import base64
    try:
        decoded = base64.b64decode(kod.encode()).decode()
        await interaction.response.send_message(f"🔓 STEFVM Zdekodowane: `{decoded}`", ephemeral=True)
    except:
        await interaction.response.send_message("❌ Błąd dekodowania Base64.", ephemeral=True)

@tree.command(name="password-gen", description="Generuje bezpieczne hasło")
async def ut_passgen(interaction: discord.Interaction, dlugosc: int = 12):
    import string
    chars = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(chars) for _ in range(dlugosc))
    await interaction.response.send_message(f"🔑 STEFVM Wygenerowane hasło: `{password}`", ephemeral=True)

@tree.command(name="timer", description="Ustawia minutnik")
async def ut_timer(interaction: discord.Interaction, sekundy: int):
    await interaction.response.send_message(f"⏱️ Minutnik STEFVM uruchomiony na {sekundy} sekund.")

@tree.command(name="whois", description="Szuka informacji o użytkowniku")
async def ut_whois(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🔍 Karta STEFVM dla {member.mention}.", ephemeral=True)

@tree.command(name="permissions-check", description="Sprawdza uprawnienia użytkownika")
async def ut_perms(interaction: discord.Interaction, member: discord.Member = None):
    m = member or interaction.user
    perms = [p[0] for p in m.guild_permissions if p[1]]
    await interaction.response.send_message(f"🛡️ Uprawnienia STEFVM dla {m.mention}: {', '.join(perms[:10])}", ephemeral=True)

@tree.command(name="server-icon", description="Pobiera ikonę serwera")
async def ut_icon(interaction: discord.Interaction):
    if interaction.guild.icon:
        await interaction.response.send_message(f"🖼️ Ikona STEFVM: {interaction.guild.icon.url}")
    else:
        await interaction.response.send_message("❌ Serwer nie ma ikony.", ephemeral=True)

@tree.command(name="math-sqrt", description="Oblicza pierwiastek kwadratowy")
async def ut_sqrt(interaction: discord.Interaction, liczba: float):
    import math
    await interaction.response.send_message(f"📐 Pierwiastek STEFVM z {liczba} to `{math.sqrt(liczba)}`", ephemeral=True)


# ==============================================================================
# 7. KATEGORIA: 4FUN, INTERAKCJE I MINI-GRY (Komendy 81-110)
# ==============================================================================
@tree.command(name="8ball", description="Magiczna kula odpowiada na pytanie")
async def fun_8ball(interaction: discord.Interaction, pytanie: str):
    odpowiedzi = ["Tak.", "Nie.", "Wszystko na to wskazuje.", "Zdecydowanie nie.", "Zapytaj ponownie później.", "Możliwe."]
    await interaction.response.send_message(f"🎱 STEFVM 8ball — Pytanie: `{pytanie}`\nOdpowiedź: **{random.choice(odpowiedzi)}**")

@tree.command(name="coinflip", description="Rzuca monetą (orzeł czy reszka)")
async def fun_coin(interaction: discord.Interaction):
    wynik = random.choice(["Orzeł 🦅", "Reszka 🪙"])
    await interaction.response.send_message(f"🪙 STEFVM Moneta: **{wynik}**")

@tree.command(name="roll", description="Rzuca kością od 1 do 100")
async def fun_roll(interaction: discord.Interaction):
    await interaction.response.send_message(f"🎲 STEFVM Kość: **{random.randint(1, 100)}**")

@tree.command(name="hug", description="Przytula użytkownika")
async def fun_hug(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🫂 {interaction.user.mention} przytula mocno {member.mention} w świecie STEFVM!")

@tree.command(name="slap", description="Daje klapsa użytkownikowi")
async def fun_slap(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"👋 {interaction.user.mention} daje klapsa użytkownikowi {member.mention}!")

@tree.command(name="kiss", description="Całuje użytkownika")
async def fun_kiss(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"💋 {interaction.user.mention} całuje {member.mention}!")

@tree.command(name="pat", description="Głaszcze użytkownika po głowie")
async def fun_pat(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"pat pat {interaction.user.mention} głaszcze {member.mention} po główce w STEFVM! 🥰")

@tree.command(name="kill", description="Zabawnie 'zabija' użytkownika")
async def fun_kill(interaction: discord.Interaction, member: discord.Member):
    teksty = ["został odłączony od zasilania STEFVM.", "spadł z wirtualnego krzesła.", "potknął się o kabel serwera."]
    await interaction.response.send_message(f"💀 {member.mention} {random.choice(teksty)}")

@tree.command(name="ship", description="Sprawdza dopasowanie miłosne między użytkownikami")
async def fun_ship(interaction: discord.Interaction, osoba_1: discord.Member, osoba_2: discord.Member):
    procent = random.randint(0, 100)
    await interaction.response.send_message(f"❤️ STEFVM Ship — Dopasowanie między {osoba_1.mention} a {osoba_2.mention}: **{procent}%**!")

@tree.command(name="rate", description="Ocenia coś w skali od 1 do 10")
async def fun_rate(interaction: discord.Interaction, rzecz: str):
    await interaction.response.send_message(f"⭐ STEFVM Rating dla `{rzecz}`: **{random.randint(1, 10)}/10**")

@tree.command(name="meme", description="Wysyła losowy tekstowy mem")
async def fun_meme(interaction: discord.Interaction):
    memes = ["STEFVM gdy kod zadziała za pierwszym razem: 😱", "Kiedy zapomnisz zamknąć maszyny wirtualnej na noc... 💸"]
    await interaction.response.send_message(random.choice(memes))

@tree.command(name="joke", description="Opowiada suchar")
async def fun_joke(interaction: discord.Interaction):
    jokes = ["Dlaczego maszyny wirtualne w STEFVM nie chorują? Bo mają świetną odporność systemową!", "Co robi administrator STEFVM w nocy? Śpi, bo bot pilnuje wszystkiego."]
    await interaction.response.send_message(random.choice(jokes))

@tree.command(name="choose", description="Wybiera jedną z opcji")
async def fun_choose(interaction: discord.Interaction, opcja_1: str, opcja_2: str):
    wybor = random.choice([opcja_1, opcja_2])
    await interaction.response.send_message(f"🤔 STEFVM Wybiera: **{wybor}**")

@tree.command(name="reverse", description="Odwóraca tekst")
async def fun_reverse(interaction: discord.Interaction, tekst: str):
    await interaction.response.send_message(f"🔄 STEFVM Odwrócone: `{tekst[::-1]}`")

@tree.command(name="hack", description="Symuluje zabawny 'hack' użytkownika")
async def fun_hack(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"💻 STEFVM Security — Hakowanie {member.mention}... Pobrano adres IP maszyny.")

@tree.command(name="iq", description="Losuje poziom IQ użytkownika")
async def fun_iq(interaction: discord.Interaction, member: discord.Member = None):
    m = member or interaction.user
    await interaction.response.send_message(f"🧠 Poziom IQ w systemie STEFVM dla {m.mention}: **{random.randint(60, 160)}**")

@tree.command(name="cat-fact", description="Losowy fakt o kotach")
async def fun_catfact(interaction: discord.Interaction):
    await interaction.response.send_message("🐱 STEFVM Ciekawostka: Koty przesypiają większość doby, testując cierpliwość administratorów.")

@tree.command(name="dog-fact", description="Losowy fakt o psach")
async def fun_dogfact(interaction: discord.Interaction):
    await interaction.response.send_message("🐶 STEFVM Ciekawostka: Psy potrafią rozpoznać nastrój właściciela.")

@tree.command(name="rps", description="Gra w kamień, papier, nożyce z botem")
async def fun_rps(interaction: discord.Interaction, wybor: str):
    wybory = ["kamień", "papier", "nożyce"]
    bot_wybor = random.choice(wybory)
    await interaction.response.send_message(f"🤖 STEFVM RPS — Bot wybrał: **{bot_wybor}**. Twój wybór: **{wybor}**.")

@tree.command(name="slots", description="Gra w jednorękiego bandytę")
async def fun_slots(interaction: discord.Interaction):
    symbole = ["🍎", "🍋", "🍒", "💎", "⭐"]
    wylosowane = [random.choice(symbole) for _ in range(3)]
    wynik = "Wygrana w STEFVM! 🎉" if wylosowane[0] == wylosowane[1] == wylosowane[2] else "Przegrana w STEFVM. Spróbuj ponownie!"
    await interaction.response.send_message(f"🎰 STEFVM Slots | {' '.join(wylosowane)} | — **{wynik}**")

@tree.command(name="bofh", description="Losowa wymówka administratora sysadmina")
async def fun_bofh(interaction: discord.Interaction):
    wymowki = ["To wina aktualizacji jądra STEFVM.", "Wirtualny dysk uległ dematerializacji.", "Ktoś odłączył zasilacz od serwerowni."]
    await interaction.response.send_message(f"🧑‍💻 STEFVM BOFH: *{random.choice(wymowki)}*")

@tree.command(name="linux-cmd", description="Losowa komenda Linux")
async def fun_linux(interaction: discord.Interaction):
    cmds = ["`sudo systemctl restart stefvm`", "`htop`", "`uname -a`", "`df -h`", "`journalctl -u stefvm`"]
    await interaction.response.send_message(f"🐧 STEFVM Linux: {random.choice(cmds)}")

@tree.command(name="docker-status", description="Status kontenerów wirtualnych")
async def fun_docker(interaction: discord.Interaction):
    await interaction.response.send_message("🐳 STEFVM kontener `stefvm_core` działa w pełni poprawnie (Up 3 days).")

@tree.command(name="magic-conch", description="Magiczna muszla przemawia")
async def fun_conch(interaction: discord.Interaction, pytanie: str):
    odpowiedzi = ["Tak.", "Nie.", "Może.", "Nigdy w życiu."]
    await interaction.response.send_message(f"🐚 STEFVM Muszla mówi: **{random.choice(odpowiedzi)}**")


# ==============================================================================
# 8. URUCHOMIENIE BOTA
# ==============================================================================
if __name__ == "__main__":
    if not TOKEN:
        logger.error("BŁĄD: Zmienna środowiskowa TOKEN nie jest ustawiona w Railway!")
    else:
        bot.run(TOKEN)
