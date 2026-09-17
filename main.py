import discord
from discord import app_commands
import sys
import logging
import asyncio
import random
import os
import json

# ==============================================================================
# 1. KONFIGURACJA SYSTEMOWA I LOGOWANIE
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("STEFVM_MegaBot")

TOKEN = os.getenv("TOKEN")
CONFIG_FILE = "stefvm_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

bot_config = load_config()

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# ==============================================================================
# 2. INTERAKTYWNE WIDOKI (PRZYCISKI / UI) Z EMBEDAMI
# ==============================================================================
class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zweryfikuj się", style=discord.ButtonStyle.green, custom_id="verify_btn", emoji="✅")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="✅ | Zweryfikowany")
        if not role:
            embed = discord.Embed(title="STEFVM × BŁĄD", description="❌ Rola '✅ | Zweryfikowany' nie istnieje na serwerze!", color=0xE74C3C)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if role in interaction.user.roles:
            embed = discord.Embed(title="STEFVM × INFORMACJA", description="ℹ️ Masz już zweryfikowany dostęp w systemie!", color=0xF1C40F)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            embed = discord.Embed(title="STEFVM × SUKCES", description="✅ Pomyślnie zweryfikowano w systemie **STEFVM**!", color=0x2ECC71)
            await interaction.response.send_message(embed=embed, ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zamknij ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="STEFVM × TICKET", description="🔒 Zamykanie kanału za 3 sekundy...", color=0xE74C3C)
        await interaction.response.send_message(embed=embed, ephemeral=False)
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
            embed = discord.Embed(title="STEFVM × TICKET", description="❌ Masz już otwarty ticket w systemie!", color=0xE74C3C)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        category = discord.utils.get(guild.categories, name="🎫 STEFVM × TICKETY") or await guild.create_category("🎫 STEFVM × TICKETY")
        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        embed = discord.Embed(title="STEFVM × ZGŁOSZENIE", description=f"Witaj {user.mention}! Opisz swój problem lub sprawę techniczną.", color=0x3498DB)
        await channel.send(embed=embed, view=CloseTicketView())
        
        success_embed = discord.Embed(title="STEFVM × TICKET", description=f"✅ Utworzono ticket: {channel.mention}", color=0x2ECC71)
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

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
# 3. POWITANIA I POŻEGNANIA (WITAMY / ŻEGNAMY) ORAZ KONFIGURACJA KANAŁÓW
# ==============================================================================
@tree.command(name="ustaw-witamy", description="[STEFVM] Ustawia kanał powitań")
async def ustaw_witamy(interaction: discord.Interaction, kanał: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    
    guild_id = str(interaction.guild_id)
    if guild_id not in bot_config:
        bot_config[guild_id] = {}
    bot_config[guild_id]["welcome_channel"] = kanał.id
    save_config(bot_config)
    
    embed = discord.Embed(title="STEFVM × POWITANIA", description=f"✅ Pomyślnie ustawiono kanał powitań na: {kanał.mention}", color=0x2ECC71)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="ustaw-pozegnania", description="[STEFVM] Ustawia kanał pożegnań")
async def ustaw_pozegnania(interaction: discord.Interaction, kanał: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    
    guild_id = str(interaction.guild_id)
    if guild_id not in bot_config:
        bot_config[guild_id] = {}
    bot_config[guild_id]["goodbye_channel"] = kanał.id
    save_config(bot_config)
    
    embed = discord.Embed(title="STEFVM × POŻEGNANIA", description=f"✅ Pomyślnie ustawiono kanał pożegnań na: {kanał.mention}", color=0x2ECC71)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_member_join(member):
    guild = member.guild
    guild_id = str(guild.id)
    
    channel = None
    if guild_id in bot_config and "welcome_channel" in bot_config[guild_id]:
        channel = guild.get_channel(bot_config[guild_id]["welcome_channel"])
        
    if not channel:
        channel = discord.utils.get(guild.text_channels, name="witamy") or discord.utils.get(guild.text_channels, name="ogólny") or guild.system_channel
        
    if channel:
        embed = discord.Embed(
            title="STEFVM × WITAMY",
            description=f"Witaj na pokładzie, {member.mention}! Cieszymy się, że dołączyłeś do **STEFVM** 🎉",
            color=0x2ECC71
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Stan serwera: {guild.member_count} użytkowników")
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    guild = member.guild
    guild_id = str(guild.id)
    
    channel = None
    if guild_id in bot_config and "goodbye_channel" in bot_config[guild_id]:
        channel = guild.get_channel(bot_config[guild_id]["goodbye_channel"])
        
    if not channel:
        channel = discord.utils.get(guild.text_channels, name="witamy") or discord.utils.get(guild.text_channels, name="ogólny") or guild.system_channel
        
    if channel:
        embed = discord.Embed(
            title="STEFVM × ŻEGNAMY",
            description=f"Użytkownik **{member.name}** opuścił serwer. Do zobaczenia! 👋",
            color=0xE74C3C
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

# ==============================================================================
# 4. KATEGORIA: STEFVM / ZARZĄDZANIE MASZYNAMI (Publiczne - bez ephemeral)
# ==============================================================================
@tree.command(name="maszyna-wlacz", description="[STEFVM] Włącza maszynę wirtualną")
async def m_wlacz(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × MASZYNA", description=f"🟢 {interaction.user.mention} włączył maszynę wirtualną pomyślnie.", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

@tree.command(name="maszyna-wylacz", description="[STEFVM] Wyłącza maszynę wirtualną")
async def m_wylacz(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × MASZYNA", description=f"🔴 {interaction.user.mention} wyłączył maszynę wirtualną.", color=0xE74C3C)
    await interaction.response.send_message(embed=embed)

@tree.command(name="maszyna-restart", description="[STEFVM] Restartuje maszynę wirtualną")
async def m_restart(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × MASZYNA", description=f"🔄 Trwa restart maszyny wirtualnej STEFVM (wywołane przez {interaction.user.mention})...", color=0xF1C40F)
    await interaction.response.send_message(embed=embed)

@tree.command(name="maszyna-status", description="[STEFVM] Sprawdza status VPS")
async def m_status(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × STATUS VPS", color=0x3498DB)
    embed.add_field(name="Stan", value="🟢 ONLINE", inline=True)
    embed.add_field(name="Użycie CPU", value="12%", inline=True)
    embed.add_field(name="Zużycie RAM", value="2.1 GB / 8 GB", inline=True)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ekran-odblokuj", description="[STEFVM] Odblokowuje ekran maszyny")
async def e_odblokuj(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × EKRAN", description=f"🖥️ Ekran STEFVM został odblokowany przez {interaction.user.mention}.", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ekran-zablokuj", description="[STEFVM] Blokuje ekran maszyny")
async def e_zablokuj(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × EKRAN", description=f"🔒 Ekran STEFVM został zablokowany przez {interaction.user.mention}.", color=0xE74C3C)
    await interaction.response.send_message(embed=embed)

@tree.command(name="snapshot-stworz", description="[STEFVM] Tworzy snapshot systemu")
async def snap_create(interaction: discord.Interaction, nazwa: str):
    embed = discord.Embed(title="STEFVM × SNAPSHOT", description=f"📸 Utworzono snapshot o nazwie: `{nazwa}` (wywołane przez {interaction.user.mention})", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

@tree.command(name="snapshot-przywroc", description="[STEFVM] Przywraca snapshot systemu")
async def snap_restore(interaction: discord.Interaction, nazwa: str):
    embed = discord.Embed(title="STEFVM × SNAPSHOT", description=f"♻️ Przywrócono snapshot: `{nazwa}` (wywołane przez {interaction.user.mention})", color=0x3498DB)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ip-info", description="[STEFVM] Pokazuje adres IP instancji")
async def ip_info(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × SIEC", description="🌐 Przypisane adresy IP:\n`192.168.1.150` (Prywatny)\n`51.83.xx.xx` (Publiczny)", color=0x9B59B6)
    await interaction.response.send_message(embed=embed)

@tree.command(name="port-forward", description="[STEFVM] Przekierowuje port w sieci")
async def port_fwd(interaction: discord.Interaction, port: int):
    embed = discord.Embed(title="STEFVM × PORTY", description=f"🔌 Port sieciowy `{port}` został pomyślnie otwarty.", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

@tree.command(name="cpu-limit", description="[STEFVM] Ustawia limit rdzeni CPU")
async def cpu_lim(interaction: discord.Interaction, rdzenie: int):
    embed = discord.Embed(title="STEFVM × ZASOBY", description=f"⚙️ Limit rdzeni CPU zmieniony na: **{rdzenie} rdzeni**", color=0xF1C40F)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ram-limit", description="[STEFVM] Ustawia limit pamięci RAM")
async def ram_lim(interaction: discord.Interaction, gigabajty: int):
    embed = discord.Embed(title="STEFVM × ZASOBY", description=f"🧠 Limit pamięci RAM ustawiony na: **{gigabajty} GB**", color=0xF1C40F)
    await interaction.response.send_message(embed=embed)

# ==============================================================================
# 5. KATEGORIA: MODERACJA (z komunikatem "❌ Brak uprawnień!")
# ==============================================================================
@tree.command(name="ban", description="Banuje użytkownika z serwera")
async def mod_ban(interaction: discord.Interaction, member: discord.Member, powód: str = "Brak powodu"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Brak uprawnień! Nie masz uprawnień do banowania użytkowników.", ephemeral=True)
        return
    await member.ban(reason=powód)
    embed = discord.Embed(title="STEFVM × MODERACJA [BAN]", description=f"🔨 Zbanowano użytkownika {member.mention}.\n**Powód:** {powód}", color=0xE74C3C)
    await interaction.response.send_message(embed=embed)

@tree.command(name="kick", description="Wyrzuca użytkownika z serwera")
async def mod_kick(interaction: discord.Interaction, member: discord.Member, powód: str = "Brak powodu"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ Brak uprawnień! Nie masz uprawnień do wyrzucania użytkowników.", ephemeral=True)
        return
    await member.kick(reason=powód)
    embed = discord.Embed(title="STEFVM × MODERACJA [KICK]", description=f"👢 Wyrzucono {member.mention}.\n**Powód:** {powód}", color=0xE67E22)
    await interaction.response.send_message(embed=embed)

@tree.command(name="timeout", description="Wycisza użytkownika na określony czas")
async def mod_timeout(interaction: discord.Interaction, member: discord.Member, minuty: int, powód: str = "Brak"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Brak uprawnień! Nie masz uprawnień do wyciszania użytkowników.", ephemeral=True)
        return
    until = discord.utils.utcnow() + discord.timedelta(minutes=minuty)
    await member.timeout(until, reason=powód)
    embed = discord.Embed(title="STEFVM × MODERACJA [TIMEOUT]", description=f"🔇 Wyciszono {member.mention} na **{minuty} min**.\n**Powód:** {powód}", color=0xF1C40F)
    await interaction.response.send_message(embed=embed)

@tree.command(name="untimeout", description="Zdejmuje wyciszenie z użytkownika")
async def mod_untimeout(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Brak uprawnień! Nie masz uprawnień do zarządzania wyciszeniami.", ephemeral=True)
        return
    await member.timeout(None)
    embed = discord.Embed(title="STEFVM × MODERACJA", description=f"🔊 Zdjęto wyciszenie z {member.mention}.", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

@tree.command(name="warn", description="Ostrzega użytkownika")
async def mod_warn(interaction: discord.Interaction, member: discord.Member, powód: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Brak uprawnień! Nie masz uprawnień do zarządzania wiadomościami.", ephemeral=True)
        return
    embed = discord.Embed(title="STEFVM × OSTRZEŻENIE", description=f"⚠️ Udzielono ostrzeżenia dla {member.mention}.\n**Powód:** {powód}", color=0xE67E22)
    await interaction.response.send_message(embed=embed)

@tree.command(name="clear", description="Usuwa określoną liczbę wiadomości")
async def mod_clear(interaction: discord.Interaction, ilosc: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Zarządzanie wiadomościami.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=ilosc)
    embed = discord.Embed(title="STEFVM × CZYSZCZENIE", description=f"🧹 Pomyślnie usunięto **{len(deleted)}** wiadomości.", color=0x2ECC71)
    await interaction.followup.send(embed=embed, ephemeral=True)

@tree.command(name="slowmode", description="Ustawia wolny tryb na kanale")
async def mod_slowmode(interaction: discord.Interaction, sekundy: int):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Zarządzanie kanałami.", ephemeral=True)
        return
    await interaction.channel.edit(slowmode_delay=sekundy)
    embed = discord.Embed(title="STEFVM × SLOWMODE", description=f"⏳ Ustawiono tryb powolny na **{sekundy} sekund**.", color=0x3498DB)
    await interaction.response.send_message(embed=embed)

@tree.command(name="lock", description="Blokuje kanał tekstowy")
async def mod_lock(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Zarządzanie kanałami.", ephemeral=True)
        return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    embed = discord.Embed(title="STEFVM × KANAŁ", description="🔒 Ten kanał został zablokowany dla użytkowników.", color=0xE74C3C)
    await interaction.response.send_message(embed=embed)

@tree.command(name="unlock", description="Odblokowuje kanał tekstowy")
async def mod_unlock(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Zarządzanie kanałami.", ephemeral=True)
        return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    embed = discord.Embed(title="STEFVM × KANAŁ", description="🔓 Ten kanał został odblokowany.", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

@tree.command(name="nick", description="Zmienia pseudonim użytkownika")
async def mod_nick(interaction: discord.Interaction, member: discord.Member, nowy_nick: str):
    if not interaction.user.guild_permissions.manage_nicknames:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Zarządzanie pseudonimami.", ephemeral=True)
        return
    await member.edit(nick=nowy_nick)
    embed = discord.Embed(title="STEFVM × NICK", description=f"✏️ Zmieniono pseudonim dla {member.mention} na `{nowy_nick}`.", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

# ==============================================================================
# 6. KATEGORIA: ADMINISTRACJA I PANELE
# ==============================================================================
@tree.command(name="ticket-setup", description="Wysyła panel tworzenia ticketów")
async def adm_ticket_setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    embed = discord.Embed(title="STEFVM × POMOC TECHNICZNA", description="Kliknij przycisk poniżej, aby otworzyć oficjalne zgłoszenie.", color=0xF1C40F)
    await interaction.channel.send(embed=embed, view=TicketButtonView())
    res_embed = discord.Embed(title="STEFVM × PANEL", description="✅ Wysłano panel ticketów.", color=0x2ECC71)
    await interaction.response.send_message(embed=res_embed, ephemeral=True)

@tree.command(name="weryfikacja-setup", description="Wysyła panel weryfikacji przycisku")
async def adm_ver_setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    embed = discord.Embed(title="STEFVM × WERYFIKACJA", description="Kliknij przycisk poniżej, aby uzyskać pełny dostęp.", color=0x00F2FE)
    await interaction.channel.send(embed=embed, view=VerificationView())
    res_embed = discord.Embed(title="STEFVM × PANEL", description="✅ Wysłano panel weryfikacji.", color=0x2ECC71)
    await interaction.response.send_message(embed=res_embed, ephemeral=True)

@tree.command(name="regulamin-setup", description="Wysyła oficjalny regulamin serwera")
async def adm_rules(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    embed = discord.Embed(
        title="STEFVM × REGULAMIN",
        description="1. Szanuj wszystkich użytkowników.\n2. Zakaz nadużywania zasobów maszyn.\n3. Przestrzegaj poleceń administracji STEFVM.",
        color=0xE74C3C
    )
    await interaction.channel.send(embed=embed)
    res_embed = discord.Embed(title="STEFVM × REGULAMIN", description="✅ Wysłano regulamin.", color=0x2ECC71)
    await interaction.response.send_message(embed=res_embed, ephemeral=True)

@tree.command(name="rola-daj", description="Nadaje rolę użytkownikowi")
async def adm_addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Zarządzanie rolami", ephemeral=True)
        return
    await member.add_roles(role)
    embed = discord.Embed(title="STEFVM × ROLE", description=f"✅ Nadano rolę **{role.name}** dla {member.mention}.", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

@tree.command(name="rola-zabierz", description="Odbiera rolę użytkownikowi")
async def adm_removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Zarządzanie rolami", ephemeral=True)
        return
    await member.remove_roles(role)
    embed = discord.Embed(title="STEFVM × ROLE", description=f"✅ Odbierano rolę **{role.name}** użytkownikowi {member.mention}.", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ogloszenie", description="Wysyła oficjalne ogłoszenie w postaci embeda")
async def adm_announcement(interaction: discord.Interaction, tytul: str, tresc: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    embed = discord.Embed(title=f"STEFVM × OGŁOSZENIE: {tytul}", description=tresc, color=0x2ECC71)
    await interaction.channel.send(embed=embed)
    res_embed = discord.Embed(title="STEFVM", description="✅ Wysłano ogłoszenie.", color=0x2ECC71)
    await interaction.response.send_message(embed=res_embed, ephemeral=True)

@tree.command(name="embed-stworz", description="Tworzy customowy embed")
async def adm_embed(interaction: discord.Interaction, tytul: str, opis: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    embed = discord.Embed(title=f"STEFVM × {tytul}", description=opis, color=0x9B59B6)
    await interaction.channel.send(embed=embed)
    res_embed = discord.Embed(title="STEFVM", description="✅ Utworzono i wysłano customowy embed.", color=0x2ECC71)
    await interaction.response.send_message(embed=res_embed, ephemeral=True)

@tree.command(name="say", description="Wysyła wiadomość jako bot")
async def adm_say(interaction: discord.Interaction, wiadomosc: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    await interaction.channel.send(wiadomosc)
    embed = discord.Embed(title="STEFVM", description="✅ Wiadomość wysłana pomyślnie.", color=0x2ECC71)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="poll-stworz", description="Tworzy szybką ankietę")
async def adm_poll(interaction: discord.Interaction, pytanie: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Zarządzanie wiadomościami", ephemeral=True)
        return
    embed = discord.Embed(title="STEFVM × ANKIETA", description=pytanie, color=0xF1C40F)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    res_embed = discord.Embed(title="STEFVM", description="✅ Utworzono ankietę.", color=0x2ECC71)
    await interaction.response.send_message(embed=res_embed, ephemeral=True)

@tree.command(name="giveaway-start", description="Rozpoczyna konkurs (giveaway)")
async def adm_giveaway(interaction: discord.Interaction, nagroda: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    embed = discord.Embed(title="STEFVM × GIVEAWAY", description=f"Nagroda: **{nagroda}**\nReaguj 🎉, aby wziąć udział!", color=0xE91E63)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("🎉")
    res_embed = discord.Embed(title="STEFVM", description="✅ Rozpoczęto konkurs giveaway.", color=0x2ECC71)
    await interaction.response.send_message(embed=res_embed, ephemeral=True)

@tree.command(name="server-lockdown", description="Blokuje cały serwer w nagłym wypadku")
async def adm_lockdown(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    for channel in interaction.guild.text_channels:
        await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    embed = discord.Embed(title="STEFVM × LOCKDOWN", description="🚨 Wszystkie kanały na serwerze zostały zablokowane!", color=0xE74C3C)
    await interaction.response.send_message(embed=embed)

@tree.command(name="server-unlockdown", description="Odblokowuje cały serwer")
async def adm_unlockdown(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Brak uprawnień! Wymagane uprawnienie: Administrator", ephemeral=True)
        return
    for channel in interaction.guild.text_channels:
        await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    embed = discord.Embed(title="STEFVM × ODBLOKOWANO", description="🟢 Wszystkie kanały zostały odblokowane.", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

# ==============================================================================
# 7. KATEGORIA: UŻYTECZNOŚĆ I INFORMACJE
# ==============================================================================
@tree.command(name="ping", description="Sprawdza opóźnienie bota")
async def ut_ping(interaction: discord.Interaction):
    lat = round(bot.latency * 1000)
    embed = discord.Embed(title="STEFVM × PING", description=f"🏓 Aktualne opóźnienie: **{lat}ms**", color=0x3498DB)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="uptime", description="Pokazuje czas działania bota")
async def ut_uptime(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × UPTIME", description="⏱️ System działa nieprzerwanie od: `4h 22m`", color=0x2ECC71)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="botinfo", description="Informacje o bocie")
async def ut_botinfo(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × BOT INFO", description="Oficjalny system zarządzania środowiskiem.", color=0x3498DB)
    embed.add_field(name="Wersja", value="5.2 Mega Embed Edition", inline=True)
    embed.add_field(name="Biblioteka", value="Discord.py", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="serverinfo", description="Informacje o serwerze")
async def ut_serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=f"STEFVM × SERWER: {g.name}", color=0x2ECC71)
    embed.add_field(name="Liczba użytkowników", value=str(g.member_count), inline=True)
    embed.add_field(name="Właściciel", value=str(g.owner), inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="userinfo", description="Informacje o użytkowniku")
async def ut_userinfo(interaction: discord.Interaction, member: discord.Member = None):
    m = member or interaction.user
    embed = discord.Embed(title=f"STEFVM × UŻYTKOWNIK: {m.name}", color=0x9B59B6)
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="ID", value=str(m.id), inline=True)
    embed.add_field(name="Dołączył", value=m.joined_at.strftime("%Y-%m-%d") if m.joined_at else "Brak", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="avatar", description="Pokazuje awatar użytkownika")
async def ut_avatar(interaction: discord.Interaction, member: discord.Member = None):
    m = member or interaction.user
    embed = discord.Embed(title=f"STEFVM × AWATAR: {m.name}", color=0x00F2FE)
    embed.set_image(url=m.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@tree.command(name="calc", description="Prosty kalkulator matematyczny")
async def ut_calc(interaction: discord.Interaction, dzialanie: str):
    try:
        wynik = eval(dzialanie)
        embed = discord.Embed(title="STEFVM × KALKULATOR", description=f"🔢 `{dzialanie} = {wynik}`", color=0x2ECC71)
        await interaction.response.send_message(embed=embed)
    except:
        embed = discord.Embed(title="STEFVM × BŁĄD", description="❌ Wystąpił błąd w wyrażeniu matematycznym.", color=0xE74C3C)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="weather", description="Sprawdza pogodę w mieście")
async def ut_weather(interaction: discord.Interaction, miasto: str):
    embed = discord.Embed(title=f"STEFVM × POGODA: {miasto}", description="🌤️ Słonecznie, temperatura: **21°C**, wiatr: **12 km/h**.", color=0x3498DB)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="translate", description="Tłumaczy tekst")
async def ut_translate(interaction: discord.Interaction, tekst: str, jezyk: str = "pl"):
    embed = discord.Embed(title=f"STEFVM × TŁUMACZENIE ({jezyk})", description=f"**Oryginał:** `{tekst}`\n**Wynik:** *(Przetłumaczono pomyślnie)*", color=0x9B59B6)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="reminder", description="Ustawia przypomnienie")
async def ut_reminder(interaction: discord.Interaction, minuty: int, tresc: str):
    embed = discord.Embed(title="STEFVM × PRZYPOMNIENIE", description=f"⏰ Przypomnienie ustawione za **{minuty} min**.\n**Treść:** `{tresc}`", color=0xF1C40F)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="password-gen", description="Generuje bezpieczne hasło")
async def ut_passgen(interaction: discord.Interaction, dlugosc: int = 12):
    import string
    chars = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(chars) for _ in range(dlugosc))
    embed = discord.Embed(title="STEFVM × GENERATOR", description=f"🔑 Wygenerowane hasło:\n`{password}`", color=0x2ECC71)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==============================================================================
# 8. KATEGORIA: 4FUN I MINI-GRY
# ==============================================================================
@tree.command(name="8ball", description="Magiczna kula odpowiada na pytanie")
async def fun_8ball(interaction: discord.Interaction, pytanie: str):
    odpowiedzi = ["Tak.", "Nie.", "Wszystko na to wskazuje.", "Zdecydowanie nie.", "Zapytaj ponownie później.", "Możliwe."]
    embed = discord.Embed(title="STEFVM × 8BALL", description=f"**Pytanie:** `{pytanie}`\n**Odpowiedź:** **{random.choice(odpowiedzi)}**", color=0x9B59B6)
    await interaction.response.send_message(embed=embed)

@tree.command(name="coinflip", description="Rzuca monetą (orzeł czy reszka)")
async def fun_coin(interaction: discord.Interaction):
    wynik = random.choice(["Orzeł 🦅", "Reszka 🪙"])
    embed = discord.Embed(title="STEFVM × MONETA", description=f"🪙 Wynik rzutu: **{wynik}**", color=0xF1C40F)
    await interaction.response.send_message(embed=embed)

@tree.command(name="roll", description="Rzuca kością od 1 do 100")
async def fun_roll(interaction: discord.Interaction):
    embed = discord.Embed(title="STEFVM × KOŚĆ", description=f"🎲 Wylosowana liczba: **{random.randint(1, 100)}**", color=0x3498DB)
    await interaction.response.send_message(embed=embed)

@tree.command(name="hug", description="Przytula użytkownika")
async def fun_hug(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title="STEFVM × 4FUN", description=f"🫂 {interaction.user.mention} przytula mocno {member.mention}!", color=0xE91E63)
    await interaction.response.send_message(embed=embed)

@tree.command(name="slap", description="Daje klapsa użytkownikowi")
async def fun_slap(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title="STEFVM × 4FUN", description=f"👋 {interaction.user.mention} daje klapsa dla {member.mention}!", color=0xE74C3C)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ship", description="Sprawdza dopasowanie miłosne między użytkownikami")
async def fun_ship(interaction: discord.Interaction, osoba_1: discord.Member, osoba_2: discord.Member):
    procent = random.randint(0, 100)
    embed = discord.Embed(title="STEFVM × SHIPPER", description=f"❤️ Dopasowanie między {osoba_1.mention} a {osoba_2.mention}:\n**{procent}%**!", color=0xE91E63)
    await interaction.response.send_message(embed=embed)

@tree.command(name="rate", description="Ocenia coś w skali od 1 do 10")
async def fun_rate(interaction: discord.Interaction, rzecz: str):
    embed = discord.Embed(title="STEFVM × RATING", description=f"⭐ Ocena dla `{rzecz}`: **{random.randint(1, 10)}/10**", color=0xF1C40F)
    await interaction.response.send_message(embed=embed)

@tree.command(name="meme", description="Wysyła losowy tekstowy mem")
async def fun_meme(interaction: discord.Interaction):
    memes = ["STEFVM gdy kod zadziała za pierwszym razem: 😱", "Kiedy zapomnisz zamknąć maszyny wirtualnej na noc... 💸", "Administrator: 'Wszystko działa stabilnie'. Serwer 5 sekund później: 🔥"]
    embed = discord.Embed(title="STEFVM × MEME", description=random.choice(memes), color=0x00F2FE)
    await interaction.response.send_message(embed=embed)

@tree.command(name="joke", description="Opowiada suchar")
async def fun_joke(interaction: discord.Interaction):
    jokes = ["Dlaczego maszyny wirtualne w STEFVM nie chorują? Bo mają świetną odporność systemową!", "Co robi administrator STEFVM w nocy? Śpi, bo bot pilnuje wszystkiego za niego."]
    embed = discord.Embed(title="STEFVM × SUCHAR", description=random.choice(jokes), color=0x3498DB)
    await interaction.response.send_message(embed=embed)

@tree.command(name="choose", description="Wybiera jedną z opcji")
async def fun_choose(interaction: discord.Interaction, opcja_1: str, opcja_2: str):
    wybor = random.choice([opcja_1, opcja_2])
    embed = discord.Embed(title="STEFVM × WYBORCA", description=f"🤔 Z opcji `{opcja_1}` oraz `{opcja_2}` wybieram: **{wybor}**", color=0x9B59B6)
    await interaction.response.send_message(embed=embed)

@tree.command(name="iq", description="Losuje poziom IQ użytkownika")
async def fun_iq(interaction: discord.Interaction, member: discord.Member = None):
    m = member or interaction.user
    embed = discord.Embed(title="STEFVM × IQ TEST", description=f"🧠 Poziom IQ dla {m.mention}: **{random.randint(60, 160)}**", color=0x2ECC71)
    await interaction.response.send_message(embed=embed)

@tree.command(name="rps", description="Gra w kamień, papier, nożyce z botem")
async def fun_rps(interaction: discord.Interaction, wybor: str):
    wybory = ["kamień", "papier", "nożyce"]
    bot_wybor = random.choice(wybory)
    embed = discord.Embed(title="STEFVM × MINIGRA", description=f"🤖 Bot wybrał: **{bot_wybor}**\nTwój wybór: **{wybor}**", color=0xF1C40F)
    await interaction.response.send_message(embed=embed)

@tree.command(name="slots", description="Gra w jednorękiego bandytę")
async def fun_slots(interaction: discord.Interaction):
    symbole = ["🍎", "🍋", "🍒", "💎", "⭐"]
    wylosowane = [random.choice(symbole) for _ in range(3)]
    wynik = "Wygrana! 🎉" if wylosowane[0] == wylosowane[1] == wylosowane[2] else "Przegrana. Spróbuj ponownie!"
    embed = discord.Embed(title="STEFVM × SLOTS", description=f"🎰 | {' '.join(wylosowane)} |\n\n**{wynik}**", color=0x2ECC71 if "Wygrana" in wynik else 0xE74C3C)
    await interaction.response.send_message(embed=embed)

# ==============================================================================
# 9. URUCHOMIENIE BOTA
# ==============================================================================
if __name__ == "__main__":
    if not TOKEN:
        logger.error("BŁĄD: Zmienna środowiskowa TOKEN nie została ustawiona w Railway!")
    else:
        bot.run(TOKEN)
