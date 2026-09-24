// A session can expire while the app is open (cookie lapses, or gets
// revoked from another tab). Any fetch() hitting a 401 bounces to /login
// rather than letting the SPA carry on against calls that will all fail.
(() => {
  const nativeFetch = window.fetch;
  window.fetch = async (...args) => {
    const res = await nativeFetch(...args);
    if (res.status === 401) location.href = '/login';
    return res;
  };
})();

// ── i18n ──
const I18N = {
  de: {
    types: { diaper:'Windel', nursing:'Stillen', bottle:'Fläschchen', sleep:'Schlaf', weight:'Gewicht', note:'Notiz', walk:'Spaziergang', clothing:'Kleidung', feeding:'Fütterung', mood:'Stimmung' },
    tab_log:'Verlauf', tab_stats:'Auswertung', tab_settings:'Einstellungen',
    modal_new:'Neuer Eintrag',
    tile_diaper:'Windel', tile_nursing:'Stillen', tile_bottle:'Fläschchen',
    tile_sleep_start:'Eingeschlafen', tile_weight:'Gewicht', tile_note:'Notiz',
    tile_walk:'Spaziergang', tile_clothing:'Kleidung wechseln', tile_walk_end:'Zurück', tile_mood:'Stimmung',
    fab_title:'Neuer Eintrag',
    lbl_time:'Zeitpunkt', lbl_note:'Notiz', lbl_type:'Art', lbl_amount:'Menge (ml)',
    lbl_content:'Inhalt', lbl_side:'Seite', lbl_start:'Beginn', lbl_end:'Ende', lbl_weight_g:'Gewicht (g)', lbl_height_cm:'Größe (cm)', lbl_mood:'Stimmung',
    opt_wet:'Nass', opt_dirty:'Schmutzig', opt_both:'Beides',
    opt_left:'Links', opt_right:'Rechts', opt_both_sides:'Beide',
    opt_pumped:'Abgepumpte Milch', opt_formula:'Formulamilch',
    opt_mood_happy:'Fröhlich', opt_mood_neutral:'Neutral', opt_mood_fussy:'Quengelig', opt_mood_crying:'Weint',
    btn_save_sleep:'Eingeschlafen speichern', btn_save:'Speichern',
    banner_since:'Schläft seit', banner_so_far:'Schlaf bisher', banner_wakeup:'Aufgewacht',
    banner_walk_since:'Spaziergang seit', banner_walk_so_far:'Spaziergang bisher',
    still_sleeping:'schläft noch', still_walking:'läuft noch',
    no_entries:'Keine Einträge für diesen Tag',
    no_baby_yet:'Noch kein Baby — füge eines in den Einstellungen hinzu, oder lass dich von jemandem hinzufügen.',
    section_last:'Letztes Ereignis', section_intervals:'Abstände',
    section_sleep:'Schlafdauer (letzte 10)', section_growth:'Wachstum',
    section_rhythm:'Typischer Tag', rhythm_days_label:'erfasste Tage',
    rhythm_hint:'Aus den letzten Wochen; unvollständig erfasste Tage bleiben außen vor',
    rhythm_not_enough:'Noch zu wenige vollständig erfasste Tage',
    rhythm_no_sleep:'Keine wiederkehrenden Schlafzeiten erkannt',
    rhythm_no_feeds:'Keine wiederkehrenden Fläschchenzeiten erkannt',
    stat_avg_sleep:'Ø Nickerchen', stat_avg_awake:'Ø wach dazwischen',
    stat_interval:'Abstand', stat_avg:'Ø diesen Tag',
    stat_awake_since:'Wach seit', stat_back_since:'Zurück seit',
    stat_asleep_since:'Schläft seit', stat_walking_since:'Läuft seit',
    no_data:'Keine Daten', not_enough_data:'Zu wenig Daten', no_sleep_data:'Noch keine Schlafdaten',
    no_growth_data:'Noch keine Gewichts-/Größendaten', growth_weight:'Gewicht', growth_height:'Größe',
    btn_add_measurement:'+ Eintrag',
    settings_quick_title:'Schnellzugriff (max. 5)', quick_max_toast:'Maximal 5 Schnellzugriffe',
    settings_baby_title:'Babys', lbl_current_baby:'Aktuell ausgewählt',
    settings_tab_baby:'Baby', settings_tab_quicklog:'Quick-Log', settings_tab_account:'Account',
    settings_tab_admin:'Admin', lbl_admin_users:'Benutzer', lbl_admin_babies:'Babys (alle)',
    lbl_admin_badge:'Admin', lbl_disabled_badge:'Deaktiviert', lbl_none:'Keine',
    lbl_owners:'Besitzer', loading:'Lädt…',
    lbl_admin_invites:'Einladungen', btn_create_invite:'Einladung erstellen',
    lbl_invite_email_optional:'E-Mail (optional)',
    lbl_invite_hint:'Ohne E-Mail funktioniert der Link für jeden, der ihn zuerst einlöst. Mit E-Mail nur für diese Adresse.',
    lbl_invite_anyone:'Jeder mit dem Link', lbl_invite_used:'Eingelöst',
    lbl_invite_expires:'Läuft ab', btn_revoke:'Widerrufen',
    lbl_invite_link_ready:'Link (einmal angezeigt)', lbl_invited_by:'Eingeladen von',
    lbl_admin_totp_required_title:'Zwei-Faktor-Authentifizierung erforderlich',
    lbl_admin_totp_required_body:'Der Admin-Bereich erfordert TOTP auf diesem Konto — ein Passwort allein genügt für den Zugriff auf die Daten aller Haushaltsmitglieder nicht. Unter Account einrichten.',
    lbl_baby_name:'Name', lbl_birthday:'Geburtstag', baby_name_placeholder:'Name des Babys',
    lbl_nap_threshold:'Schlafschwelle', lbl_minutes:'Minuten',
    nap_threshold_hint:'Schlafeinträge unter diesem Wert zählen als Nickerchen, längere als Nachtschlaf. Bei Neugeborenen niedriger ansetzen, mit dem Alter erhöhen.',
    lbl_bottle_default:'Standard-Inhalt (Fläschchen)', opt_bottle_ask:'Jedes Mal wählen',
    bottle_default_hint:'Beim Fläschchen-Eintrag ist dieser Inhalt vorausgewählt.',
    baby_fallback:'Baby', btn_add_baby:'Baby hinzufügen', btn_delete:'Löschen',
    confirm_delete_baby:'Dieses Baby und alle seine Einträge unwiderruflich löschen?',
    confirm_remove_access:'Zugriff für diese Person entfernen?',
    toast_no_name:'Bitte Namen angeben', toast_not_an_image:'Bitte ein Bild auswählen',
    btn_remove_photo:'Foto entfernen', lbl_crop_photo:'Foto zuschneiden',
    crop_hint:'Ziehen zum Verschieben, Schieberegler zum Zoomen.',
    btn_cancel:'Abbrechen', btn_use_photo:'Foto verwenden',
    settings_security_title:'Sicherheit', btn_logout:'Abmelden', lbl_display_name:'Anzeigename',
    member_since:'Dabei seit', last_login:'Letzte Anmeldung',
    settings_logging_title:'Erfassung', show_notes_label:'Notizfeld in Dialogen',
    show_notes_hint:'Zeigt ein Textfeld für eine Notiz beim Anlegen und Bearbeiten von Einträgen.',
    settings_notify_title:'Erinnerungen', notify_rhythm_label:'Aufwach- & Fläschchen-Erinnerung',
    notify_hint:'Push kurz bevor das Baby üblicherweise aufwacht oder das nächste Fläschchen fällig ist.',
    notify_unavailable:'Push ist auf diesem Server nicht eingerichtet.',
    notify_denied:'Benachrichtigungen wurden abgelehnt — im Browser erlauben.',
    notify_unsupported:'Dieser Browser unterstützt keine Push-Benachrichtigungen.',
    settings_totp_title:'Zwei-Faktor-Authentifizierung (TOTP)',
    totp_enabled_sub:'Aktiviert', totp_disabled_sub:'Nicht aktiviert',
    btn_disable:'Deaktivieren', btn_enable:'Aktivieren', btn_confirm:'Bestätigen',
    totp_code_placeholder:'6-stelliger Code',
    settings_passkeys_title:'Passkeys', no_passkeys:'Noch keine Passkeys',
    btn_add_passkey:'Passkey hinzufügen',
    prompt_password_to_disable:'Passwort zum Deaktivieren eingeben',
    settings_tokens_title:'API-Tokens', no_tokens:'Noch keine Tokens',
    tokens_hint:'Für Skripte oder externe Tools. Ein Token gewährt vollen Zugriff auf dein Konto.',
    last_used:'Zuletzt genutzt', never_used:'Nie', btn_add_token:'Token erstellen',
    prompt_token_name:'Name für dieses Token', lbl_new_token:'Neues Token',
    token_name_placeholder:'z. B. Laptop-Skript',
    token_shown_once:'Dieses Token wird nur jetzt angezeigt — kopiere es, bevor du diese Seite verlässt.',
    confirm_delete_token:'Dieses Token widerrufen?',
    prompt_passkey_name:'Name für diesen Passkey',
    settings_danger_title:'Gefahrenzone', btn_delete_account:'Konto löschen',
    delete_account_hint:'Löscht dein Konto dauerhaft. Nicht möglich, solange du alleiniger Besitzer eines Babys bist.',
    prompt_password_to_delete_account:'Passwort zum Löschen eingeben',
    confirm_delete_account:'Dein Konto unwiderruflich löschen?',
    role_owner:'Besitzer', role_editor:'Bearbeiter', role_viewer:'Betrachter',
    btn_manage_access:'Zugriff verwalten', btn_remove:'Entfernen', btn_invite:'Hinzufügen',
    lbl_shared_with:'Geteilt mit', lbl_profile:'Profil', lbl_selected:'gewählt',
    lbl_baby_creator:'Ersteller · Zugriff kann nicht geändert werden',
    quick_hint:'Wähle bis zu 5 Aktionen, die du direkt neben dem Plus-Button antippen kannst.',
    quick_footnote:'Alle anderen Aktionen bleiben über das große Plus erreichbar.',
    lbl_invite_email:'E-Mail', lbl_role:'Rolle',
    bd_welcome:'Willkommen', bd_happy:'🎉 Alles Gute',
    bd_born_today: name=>`${name} ist heute geboren`,
    bd_month_label: n=>`${n}-Monats-Tag`,
    bd_months_old: a=>`${a.name} ist heute ${a.n} Monate alt`,
    bd_years_old: a=>`${a.name} ist heute ${a.n} ${a.n === 1 ? 'Jahr' : 'Jahre'} alt`,
    export_title:'Export', range_today:'Heute', range_week:'Diese Woche', range_month:'Diesen Monat', range_custom:'Frei wählen',
    view_list:'Liste', view_timeline:'Zeitleiste', tl_now:'JETZT',
    btn_open_report:'Bericht öffnen', btn_download_csv:'CSV herunterladen',
    today:'Heute', yesterday:'Gestern',
    just_now:'gerade eben',
    ago_min: n=>`vor ${n} min`, ago_hour: n=>`vor ${n} h`, ago_day: n=>`vor ${n} d`,
    confirm_delete:'Eintrag löschen?',
    toast_no_time:'Bitte Zeitpunkt angeben', toast_deleted:'Gelöscht',
    toast_no_measurement:'Bitte Gewicht oder Größe angeben',
    toast_error:'Fehler beim Speichern', toast_saved:'✓ Gespeichert',
    toast_offline:'Offline – nicht gespeichert', offline_bar:'Offline – gespeicherter Stand',
    toast_queued:'Offline gespeichert – wird übertragen', pending_tag:'nicht gesendet',
    toast_sync_failed: n=>`${n} Einträge konnten nicht übertragen werden`,
    toast_wakeup: dur=>`Aufgewacht – ${dur} Schlaf`,
    toast_walk_end: dur=>`Zurück – ${dur} Spaziergang`,
    diaper_count: n=>`Windeln: ${n}`,
    diaper_poo_count: n=>`Kacka: ${n}`,
    feeding_ml: n=>`Fläschchen: ${n} ml`,
    lang_switch:'EN',
  },
  en: {
    types: { diaper:'Diaper', nursing:'Nursing', bottle:'Bottle', sleep:'Sleep', weight:'Weight', note:'Note', walk:'Walk', clothing:'Clothing', feeding:'Feeding', mood:'Mood' },
    tab_log:'Log', tab_stats:'Stats', tab_settings:'Settings',
    modal_new:'New Entry',
    tile_diaper:'Diaper', tile_nursing:'Nursing', tile_bottle:'Bottle',
    tile_sleep_start:'Fell asleep', tile_weight:'Weight', tile_note:'Note',
    tile_walk:'Walk', tile_clothing:'Clothing change', tile_walk_end:'Back', tile_mood:'Mood',
    fab_title:'New Entry',
    lbl_time:'Time', lbl_note:'Note', lbl_type:'Type', lbl_amount:'Amount (ml)',
    lbl_content:'Content', lbl_side:'Side', lbl_start:'Start', lbl_end:'End', lbl_weight_g:'Weight (g)', lbl_height_cm:'Height (cm)', lbl_mood:'Mood',
    opt_wet:'Wet', opt_dirty:'Dirty', opt_both:'Both',
    opt_left:'Left', opt_right:'Right', opt_both_sides:'Both',
    opt_pumped:'Pumped milk', opt_formula:'Formula',
    opt_mood_happy:'Happy', opt_mood_neutral:'Neutral', opt_mood_fussy:'Fussy', opt_mood_crying:'Crying',
    btn_save_sleep:'Save fell asleep', btn_save:'Save',
    banner_since:'Sleeping since', banner_so_far:'sleep so far', banner_wakeup:'Woke up',
    banner_walk_since:'Walking since', banner_walk_so_far:'walk so far',
    still_sleeping:'still sleeping', still_walking:'still walking',
    no_entries:'No entries for this day',
    no_baby_yet:'No baby yet — add one in Settings, or get added by someone who has one.',
    section_last:'Last event', section_intervals:'Intervals',
    section_sleep:'Sleep duration (last 10)', section_growth:'Growth',
    section_rhythm:'Typical day', rhythm_days_label:'tracked days',
    rhythm_hint:'Learned from the last few weeks; partly untracked days are left out',
    rhythm_not_enough:'Not enough fully tracked days yet',
    rhythm_no_sleep:'No recurring sleep times found',
    rhythm_no_feeds:'No recurring bottle times found',
    stat_avg_sleep:'Avg nap duration', stat_avg_awake:'Avg awake in between',
    stat_interval:'Interval', stat_avg:'avg this day',
    stat_awake_since:'Awake since', stat_back_since:'Back since',
    stat_asleep_since:'Asleep since', stat_walking_since:'Walking since',
    no_data:'No data', not_enough_data:'Not enough data', no_sleep_data:'No sleep data yet',
    no_growth_data:'No weight/height data yet', growth_weight:'Weight', growth_height:'Height',
    btn_add_measurement:'+ Entry',
    settings_quick_title:'Quick actions (max 5)', quick_max_toast:'Max 5 quick actions',
    settings_baby_title:'Babies', lbl_current_baby:'Currently selected',
    settings_tab_baby:'Baby', settings_tab_quicklog:'Quick-Log', settings_tab_account:'Account',
    settings_tab_admin:'Admin', lbl_admin_users:'Users', lbl_admin_babies:'Babies (all)',
    lbl_admin_badge:'Admin', lbl_disabled_badge:'Disabled', lbl_none:'None',
    lbl_owners:'Owners', loading:'Loading…',
    lbl_admin_invites:'Invites', btn_create_invite:'Create invite',
    lbl_invite_email_optional:'Email (optional)',
    lbl_invite_hint:"Without an email the link works for whoever redeems it first. With one, only that address can use it.",
    lbl_invite_anyone:'Anyone with the link', lbl_invite_used:'Used',
    lbl_invite_expires:'Expires', btn_revoke:'Revoke',
    lbl_invite_link_ready:'Link (shown once)', lbl_invited_by:'Invited by',
    lbl_admin_totp_required_title:'Two-factor authentication required',
    lbl_admin_totp_required_body:"The admin area requires TOTP on this account — a password alone isn't enough to reach every household member's data. Set it up under Account.",
    lbl_baby_name:'Name', lbl_birthday:'Birthday', baby_name_placeholder:"Baby's name",
    lbl_nap_threshold:'Nap threshold', lbl_minutes:'minutes',
    nap_threshold_hint:'Sleep entries shorter than this count as a nap in stats; longer ones count as night sleep. Lower this for a newborn, raise it as naps consolidate.',
    lbl_bottle_default:'Default bottle content', opt_bottle_ask:'Choose each time',
    bottle_default_hint:'Preselected as the content when you log a bottle.',
    baby_fallback:'Baby', btn_add_baby:'Add baby', btn_delete:'Delete',
    confirm_delete_baby:'Permanently delete this baby and all its entries?',
    confirm_remove_access:'Remove this person\'s access?',
    toast_no_name:'Please enter a name', toast_not_an_image:'Please choose an image',
    btn_remove_photo:'Remove photo', lbl_crop_photo:'Crop photo',
    crop_hint:'Drag to reposition, use the slider to zoom.',
    btn_cancel:'Cancel', btn_use_photo:'Use photo',
    settings_security_title:'Security', btn_logout:'Log out', lbl_display_name:'Display name',
    member_since:'Member since', last_login:'Last login',
    settings_logging_title:'Logging', show_notes_label:'Note field in dialogs',
    show_notes_hint:'Shows a free-text note field when adding or editing an entry.',
    settings_notify_title:'Reminders', notify_rhythm_label:'Wake & bottle reminders',
    notify_hint:'A push shortly before the baby usually wakes or the next bottle is due.',
    notify_unavailable:"Push isn't set up on this server.",
    notify_denied:'Notifications were blocked — allow them in the browser.',
    notify_unsupported:'This browser has no push support.',
    settings_totp_title:'Two-factor authentication (TOTP)',
    totp_enabled_sub:'Enabled', totp_disabled_sub:'Not enabled',
    btn_disable:'Disable', btn_enable:'Enable', btn_confirm:'Confirm',
    totp_code_placeholder:'6-digit code',
    settings_passkeys_title:'Passkeys', no_passkeys:'No passkeys yet',
    btn_add_passkey:'Add passkey',
    prompt_password_to_disable:'Enter your password to disable',
    prompt_passkey_name:'Name for this passkey',
    settings_tokens_title:'API tokens', no_tokens:'No tokens yet',
    tokens_hint:'For scripts or external tools. A token grants full access to your account.',
    last_used:'Last used', never_used:'Never', btn_add_token:'Create token',
    prompt_token_name:'Name for this token', lbl_new_token:'New token',
    token_name_placeholder:'e.g. Laptop script',
    token_shown_once:"This token is shown only now — copy it before leaving this page.",
    confirm_delete_token:'Revoke this token?',
    settings_danger_title:'Danger zone', btn_delete_account:'Delete account',
    delete_account_hint:"Permanently deletes your account. Not possible while you're the sole owner of a baby.",
    prompt_password_to_delete_account:'Enter your password to delete your account',
    confirm_delete_account:'Permanently delete your account?',
    role_owner:'Owner', role_editor:'Editor', role_viewer:'Viewer',
    btn_manage_access:'Manage access', btn_remove:'Remove', btn_invite:'Add',
    lbl_shared_with:'Shared with', lbl_profile:'Profile', lbl_selected:'selected',
    lbl_baby_creator:"Creator · access can't be changed",
    quick_hint:'Choose up to 5 actions you can tap right next to the plus button.',
    quick_footnote:'Every other action is still one tap away through the big plus.',
    lbl_invite_email:'Email', lbl_role:'Role',
    bd_welcome:'Welcome', bd_happy:'🎉 Happy birthday',
    bd_born_today: name=>`${name} was born today`,
    bd_month_label: n=>`Happy ${n}-month day`,
    bd_months_old: a=>`${a.name} is ${a.n} months old today`,
    bd_years_old: a=>`${a.name} is ${a.n} ${a.n === 1 ? 'year' : 'years'} old today`,
    export_title:'Export', range_today:'Today', range_week:'This week', range_month:'This month', range_custom:'Custom',
    view_list:'List', view_timeline:'Timeline', tl_now:'NOW',
    btn_open_report:'Open report', btn_download_csv:'Download CSV',
    today:'Today', yesterday:'Yesterday',
    just_now:'just now',
    ago_min: n=>`${n} min ago`, ago_hour: n=>`${n} h ago`, ago_day: n=>`${n} d ago`,
    confirm_delete:'Delete entry?',
    toast_no_time:'Please enter a time', toast_deleted:'Deleted',
    toast_no_measurement:'Please enter weight or height',
    toast_error:'Error saving', toast_saved:'✓ Saved',
    toast_offline:'Offline — not saved', offline_bar:'Offline — showing saved data',
    toast_queued:'Saved offline — will sync', pending_tag:'not sent',
    toast_sync_failed: n=>`${n} entries could not be synced`,
    toast_wakeup: dur=>`Woke up – ${dur} sleep`,
    toast_walk_end: dur=>`Back – ${dur} walk`,
    diaper_count: n=>`Diapers: ${n}`,
    diaper_poo_count: n=>`Poo: ${n}`,
    feeding_ml: n=>`Bottle: ${n} ml`,
    lang_switch:'DE',
  },
};

// stored meta values → translated display (both old German keys and neutral keys)
const META_VALS = {
  nass:{de:'Nass',en:'Wet'}, schmutzig:{de:'Schmutzig',en:'Dirty'}, beides:{de:'Beides',en:'Both'},
  wet:{de:'Nass',en:'Wet'}, dirty:{de:'Schmutzig',en:'Dirty'}, both:{de:'Beides',en:'Both'},
  links:{de:'Links',en:'Left'}, rechts:{de:'Rechts',en:'Right'}, beide:{de:'Beide',en:'Both'},
  left:{de:'Links',en:'Left'}, right:{de:'Rechts',en:'Right'},
  abgepumpt:{de:'Abgepumpt',en:'Pumped'}, formula:{de:'Formula',en:'Formula'},
  happy:{de:'Fröhlich',en:'Happy'}, neutral:{de:'Neutral',en:'Neutral'}, fussy:{de:'Quengelig',en:'Fussy'}, crying:{de:'Weint',en:'Crying'},
};

const ICONS = {
  diaper: '<path d="M4.5 8h15c.3 0 .5.2.5.5C20 13.7 16.4 18 12 18S4 13.7 4 8.5c0-.3.2-.5.5-.5Z"/><path d="M6.2 8.8c1.7 1 3.8 1.5 5.8 1.5s4.1-.5 5.8-1.5"/><path d="M3 9.3h1.7M19.3 9.3H21"/>',
  nursing: '<path d="M12 20.5S4.5 15.8 4.5 10.2A4.2 4.2 0 0 1 12 7.4a4.2 4.2 0 0 1 7.5 2.8c0 5.6-7.5 10.3-7.5 10.3Z"/>',
  bottle: '<rect x="7" y="8.5" width="10" height="11.5" rx="3"/><path d="M9.3 8.5V6.6a1 1 0 0 1 1-1h3.4a1 1 0 0 1 1 1v1.9"/><path d="M10.3 5.6c0-1.5.8-2.6 1.7-2.6s1.7 1.1 1.7 2.6"/><path d="M9 12.3h1.6M9 15.3h1.6M9 18.3h1.6"/>',
  feeding: '<rect x="7" y="8.5" width="10" height="11.5" rx="3"/><path d="M9.3 8.5V6.6a1 1 0 0 1 1-1h3.4a1 1 0 0 1 1 1v1.9"/><path d="M10.3 5.6c0-1.5.8-2.6 1.7-2.6s1.7 1.1 1.7 2.6"/><path d="M9 12.3h1.6M9 15.3h1.6M9 18.3h1.6"/>',
  sleep: '<path d="M20 14.3A8 8 0 1 1 9.7 4a6.3 6.3 0 0 0 10.3 10.3Z"/>',
  zzz: '<path d="M3 15h6l-6 6h6"/><path d="M10 9h5l-5 5h5"/><path d="M16 4h4l-4 4h4"/>',
  walk: '<ellipse cx="15" cy="16" rx="2.6" ry="3.6" transform="rotate(12 15 16)"/><circle cx="12.6" cy="12.4" r=".9"/><circle cx="14" cy="11.3" r=".95"/><circle cx="15.6" cy="11.1" r=".95"/><circle cx="17" cy="11.8" r=".85"/><ellipse cx="8" cy="7.5" rx="2" ry="2.8" transform="rotate(-12 8 7.5)"/><circle cx="6" cy="4.6" r=".7"/><circle cx="7.3" cy="3.8" r=".75"/><circle cx="8.7" cy="3.9" r=".7"/>',
  weight: '<circle cx="12" cy="12" r="8.2"/><path d="M12 8.6v3.8l2.6 1.6"/>',
  note: '<path d="M6 3.5h9L19.5 8v12.5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z"/><path d="M8.5 12h7M8.5 15.5h7M8.5 8.5h3"/>',
  clothing: '<path d="M8.5 4 5.8 5.7a1.4 1.4 0 0 0-.5 1.8L6.6 10l1.9-.9v9.4a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1V9.1l1.9.9 1.3-2.5a1.4 1.4 0 0 0-.5-1.8L15.5 4a4 4 0 0 1-7 0Z"/>',
  sun: '<circle cx="12" cy="12" r="4.2"/><path d="M12 3v2.2M12 18.8V21M21 12h-2.2M5.2 12H3M18.4 5.6l-1.5 1.5M7.1 16.9l-1.5 1.5M18.4 18.4l-1.5-1.5M7.1 7.1 5.6 5.6"/>',
  home: '<path d="M4 11 12 4l8 7"/><path d="M6 10v9.5a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V10"/><path d="M10 20.5V15h4v5.5"/>',
  mood: '<circle cx="12" cy="12" r="8.3"/><circle cx="9.2" cy="10.3" r=".9"/><circle cx="14.8" cy="10.3" r=".9"/><path d="M8.3 14.5c1 1.6 2.3 2.5 3.7 2.5s2.7-.9 3.7-2.5"/>',
  mood_happy: '<circle cx="12" cy="12" r="8.3"/><circle cx="9.2" cy="10.3" r=".9"/><circle cx="14.8" cy="10.3" r=".9"/><path d="M8.3 14.2c1 1.7 2.3 2.6 3.7 2.6s2.7-.9 3.7-2.6"/>',
  mood_neutral: '<circle cx="12" cy="12" r="8.3"/><circle cx="9.2" cy="10.3" r=".9"/><circle cx="14.8" cy="10.3" r=".9"/><path d="M9 15h6"/>',
  mood_fussy: '<circle cx="12" cy="12" r="8.3"/><circle cx="9.2" cy="10.3" r=".9"/><circle cx="14.8" cy="10.3" r=".9"/><path d="M9 15.4c.8-.9 1.8-1.3 3-1.3s2.2.4 3 1.3"/>',
  mood_crying: '<circle cx="12" cy="12" r="8.3"/><path d="M8.2 10.9c.4-.8 1.3-.8 1.7 0"/><path d="M14.1 10.9c.4-.8 1.3-.8 1.7 0"/><path d="M8.5 16c1-1.4 2.2-2.1 3.5-2.1s2.5.7 3.5 2.1"/>',
  cake: '<path d="M4 20.5h16"/><path d="M4.5 20.5v-5.2c0-1 .8-1.8 1.8-1.8h11.4c1 0 1.8.8 1.8 1.8v5.2"/><path d="M4.5 16.6c1.2 0 1.2 1.2 2.5 1.2s1.2-1.2 2.5-1.2 1.2 1.2 2.5 1.2 1.2-1.2 2.5-1.2 1.2 1.2 2.5 1.2 1.3-1.2 2.5-1.2"/><path d="M12 13.5v-3"/><path d="M12 9.6c-.7-.5-.7-1.5 0-2.3.7.8.7 1.8 0 2.3Z"/>',
  check: '<path d="M5 13l4 4L19 7"/>',
  person: '<circle cx="12" cy="8.5" r="3.5"/><path d="M5 20c0-4 3-6.5 7-6.5s7 2.5 7 6.5"/>',
  shield: '<path d="M12 3l7 3v6c0 4.8-3 8.5-7 9.5C8 20.5 5 16.8 5 12V6l7-3Z"/>',
  key: '<circle cx="8" cy="15" r="3.2"/><path d="M10.3 12.7 18 5M15 8l2 2M17.5 5.5l2 2"/>',
  code: '<path d="M9 8 4 12l5 4M15 8l5 4-5 4"/>',
  bell: '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.6 1.8a.6.6 0 0 1-.5 1H4.9a.6.6 0 0 1-.5-1Z"/><path d="M10 21a2 2 0 0 0 4 0"/>',
};
function icon(name) { return `<svg viewBox="0 0 24 24" class="ic">${ICONS[name] || ''}</svg>`; }
function typeIcon(name) { return name === 'sleep' ? icon('zzz') : icon(name); }
function typeTint(type) {
  if (type === 'sleep') return 'sleep';
  if (type === 'walk') return 'walk';
  if (type === 'nursing' || type === 'bottle' || type === 'feeding') return 'feed';
  if (type === 'mood') return 'mood';
  return 'accent';
}

let lang = localStorage.getItem('lang') || (navigator.language.startsWith('de') ? 'de' : 'en');

function t(key, arg) {
  const val = I18N[lang][key];
  return typeof val === 'function' ? val(arg) : (val ?? key);
}
function tMeta(val) { return (META_VALS[val] && META_VALS[val][lang]) || val; }
function getType(key) { return { label: (I18N[lang].types[key] || key), icon: key in ICONS ? key : 'note' }; }

function switchLang() {
  lang = lang === 'de' ? 'en' : 'de';
  localStorage.setItem('lang', lang);
  initUI();
  loadLog();
  renderBirthdayBanner();
  renderBabySwitcherLabel();
  renderTimelineLegend(logView === 'timeline');
  if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
  if (document.getElementById('tab-settings').classList.contains('active')) loadSettings();
}

function initUI() {
  document.getElementById('html-root').lang = lang;
  document.getElementById('lang-btn').textContent = t('lang_switch');
  document.querySelector('#tab-btn-log .tab-lbl').textContent = t('tab_log');
  document.querySelector('#tab-btn-stats .tab-lbl').textContent = t('tab_stats');
  document.querySelector('#tab-btn-settings .tab-lbl').textContent = t('tab_settings');
  document.getElementById('fab').title = t('fab_title');
  ['diaper','nursing','bottle','sleep_start','weight','note','walk','clothing','mood'].forEach(k => {
    const el = document.getElementById('tile-'+k);
    if (el) el.querySelector('.t-label').textContent = t('tile_'+k);
  });
  document.getElementById('export-title').textContent = t('export_title');
  document.querySelector('.range-pill[data-range=today]').textContent = t('range_today');
  document.querySelector('.range-pill[data-range=week]').textContent = t('range_week');
  document.querySelector('.range-pill[data-range=month]').textContent = t('range_month');
  document.querySelector('.range-pill[data-range=custom]').textContent = t('range_custom');
  document.querySelector('#log-view-toggle .range-pill[data-view=list]').textContent = t('view_list');
  document.querySelector('#log-view-toggle .range-pill[data-view=timeline]').textContent = t('view_timeline');
  document.getElementById('export-report-btn').textContent = t('btn_open_report');
  document.getElementById('export-csv-btn').textContent = t('btn_download_csv');
}

const USER_COLORS = [
  '#c8602a','#3a7d6b','#5b4fa8','#b04040','#2e6fa8',
  '#8a6a1f','#4a7a2e','#8a2e6a','#2e6a8a','#6a3a2e',
];

let userColorMap = {};
let colorIndex = 0;
let currentDate = storedDate();
let openSleepEntry = null;
let openWalkEntry = null;
let selectedType = null;
let currentEntries = [];
let editEntryId = null;

// Whether the app is offline is decided by what the network actually did,
// not by navigator.onLine — that reports a link, not a reachable server,
// and stays true for a page the service worker served from its cache.
// Wrapping fetch once keeps the check out of ~30 call sites.
const rawFetch = window.fetch.bind(window);
window.fetch = async (...args) => {
  try {
    const res = await rawFetch(...args);
    setOffline(!!res.headers.get('X-Offline'));
    return res;
  } catch (err) {
    setOffline(true);
    throw err;
  }
};

// ── Offline queue ──
// Entries added without a network wait here until one comes back. Only
// additions queue: an entry carries the time it happened, so sending it
// late records the same thing as sending it on time, and two phones adding
// entries never have to agree on anything. Edits and deletes still need
// the server, since those do depend on what everyone else has done since.
const PENDING_KEY = 'pendingEntries';
let myName = '';
let showNoteFields = true;
let syncing = false;

function pendingAll() {
  try { return JSON.parse(localStorage.getItem(PENDING_KEY)) || []; } catch { return []; }
}
function pendingSave(list) {
  localStorage.setItem(PENDING_KEY, JSON.stringify(list));
}
function pendingForDay(day, babyId) {
  return pendingAll()
    .filter(p => p.baby_id === babyId && localDate(p.body.ts_start) === day)
    .map(p => ({ ...p.body, localId: p.localId, username: myName, pending: true }));
}
/** An unsynced sleep or walk still counts as open, or the quick button
 *  would offer to start a second one on top of it. */
function pendingOpen(type) {
  const open = pendingAll().filter(
    p => p.baby_id === currentBabyId && p.body.type === type && !p.body.ts_end
  );
  const p = open[open.length - 1];
  return p ? { ...p.body, localId: p.localId, pending: true } : null;
}
function dropPending(localId) {
  pendingSave(pendingAll().filter(p => p.localId !== localId));
  loadLog();
}
/** Finish a sleep or walk that hasn't been sent yet, in the queue rather
 *  than over the wire — the server has no row to patch yet. */
function closePending(entry, tsEnd) {
  if (!entry?.pending) return false;
  const list = pendingAll();
  const item = list.find(p => p.localId === entry.localId);
  if (!item) return false;
  item.body.ts_end = tsEnd;
  pendingSave(list);
  return true;
}

/** Post an entry, or keep it for later when there is no network. */
async function createEntry(body) {
  let res = null;
  try {
    res = await fetch('/api/entries?baby_id=' + currentBabyId, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch { res = null; }
  if (res && res.ok) return { saved: await res.json() };
  if (!res || res.headers.get('X-Offline')) {
    const item = {
      localId: 'p' + Date.now() + Math.random().toString(36).slice(2, 6),
      baby_id: currentBabyId,
      body,
    };
    pendingSave(pendingAll().concat([item]));
    toast(t('toast_queued'));
    return { queued: item };
  }
  return { failed: res };
}

/** Replay the queue oldest first, stopping at the first sign the network
 *  is still gone so the order they were logged in survives. */
async function syncPending() {
  if (syncing || !pendingAll().length) return;
  syncing = true;
  let synced = 0, rejected = 0;
  try {
    for (const item of pendingAll()) {
      let res;
      try {
        res = await fetch('/api/entries?baby_id=' + item.baby_id, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item.body),
        });
      } catch { break; }
      if (!res.ok && res.headers.get('X-Offline')) break;
      // A refusal — an entry queued past the server's backdating window,
      // say — would otherwise block everything behind it forever.
      if (res.ok) synced++; else rejected++;
      pendingSave(pendingAll().filter(p => p.localId !== item.localId));
    }
  } finally {
    syncing = false;
  }
  if (rejected) toast(t('toast_sync_failed', rejected));
  if (synced || rejected) loadLog();
}

// ── Date helpers ──
function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
}
function pad(n) { return String(n).padStart(2,'0'); }
// The day the user was last looking at, so a reload doesn't snap back to
// today. Only honoured for the calendar day it was stored on: once
// midnight passes, opening the app lands on the new today rather than
// getting stuck on what is now yesterday (e.g. a sleep still running
// from the night before).
function storedDate() {
  const d = localStorage.getItem('logDate');
  const savedOn = localStorage.getItem('logDateDay');
  if (d && /^\d{4}-\d{2}-\d{2}$/.test(d) && savedOn === todayStr() && d <= todayStr()) {
    return d;
  }
  return todayStr();
}
// ── UTC storage, local display ──
// Timestamps travel and are stored as an explicit UTC instant
// ('2026-08-26T05:23Z'); everything the user sees or types is that instant
// in this browser's own timezone. Conversion happens only at the API
// boundary, so form inputs stay plain local wall-clock throughout.
function nowLocal() {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function nowUtc() {
  return new Date().toISOString().slice(0, 16) + 'Z';
}
/** 'YYYY-MM-DDTHH:MM' in local time -> stored UTC instant. */
function toUtc(localDT) {
  if (!localDT) return '';
  const d = new Date(localDT);          // no zone suffix: parsed as local
  return isNaN(d) ? '' : d.toISOString().slice(0, 16) + 'Z';
}
/** Stored UTC instant -> 'YYYY-MM-DDTHH:MM' in local time, for inputs. */
function toLocalDT(utcIso) {
  if (!utcIso) return '';
  const d = new Date(utcIso);
  if (isNaN(d)) return '';
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
/** Stored UTC instant -> 'YYYY-MM-DD' local calendar date. */
function localDate(utcIso) {
  if (!utcIso) return '';
  const d = new Date(utcIso);
  if (isNaN(d)) return '';
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
}
/** Minutes past local midnight for a stored UTC instant. */
function localMinutes(utcIso) {
  const d = new Date(utcIso);
  return d.getHours() * 60 + d.getMinutes();
}
// Split/join instead of relying on <input type="datetime-local">, whose time
// step is unreliable on Android WebView/Chrome — plain date+time inputs work everywhere.
function splitDT(dt) {
  if (!dt) return { date: '', time: '' };
  const [date, time] = dt.split('T');
  return { date, time: time || '' };
}
function joinDT(date, time) {
  return (date && time) ? `${date}T${time}` : '';
}
function dtField(idPrefix, label, value) {
  const { date, time } = splitDT(value);
  return `
    <div class="field"><label>${label}</label>
      <div class="dt-row">
        <input type="date" id="${idPrefix}-date" value="${date}">
        <input type="time" id="${idPrefix}-time" value="${time}">
      </div>
    </div>`;
}
function readDT(idPrefix) {
  const date = document.getElementById(`${idPrefix}-date`)?.value;
  const time = document.getElementById(`${idPrefix}-time`)?.value;
  return joinDT(date, time);
}
/** The note textarea added to every non-note dialog — omitted when the
 *  account has turned it off in Settings, unless the entry already carries
 *  a note (from before it was turned off, or another device), so editing
 *  never hides text you'd otherwise have no way to see or clear. The
 *  standalone Note entry type always has its own field regardless — that
 *  one field is the whole point of it. */
function noteFieldHtml(value = '', rows = 2) {
  if (!showNoteFields && !value) return '';
  return `<div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="${rows}">${value}</textarea></div>`;
}
function fmtDate(s) {
  const [y,m,d] = s.split('-');
  const today = todayStr();
  const yesterday = (() => { const dt = new Date(); dt.setDate(dt.getDate()-1); return `${dt.getFullYear()}-${pad(dt.getMonth()+1)}-${pad(dt.getDate())}`; })();
  if (s === today) return t('today');
  if (s === yesterday) return t('yesterday');
  return `${d}.${m}.${y}`;
}
function fmtStartTime(iso) {
  const d = localDate(iso);
  return d === currentDate ? fmtTime(iso) : `${fmtDate(d)} ${fmtTime(iso)}`;
}
function fmtTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function fmtDur(min) {
  if (!min && min !== 0) return '—';
  const h = Math.floor(min/60), m = Math.round(min%60);
  return h === 0 ? `${m} min` : `${h}h ${m}m`;
}
function durMin(a, b) { return Math.abs((new Date(b)-new Date(a))/60000); }
function fmtAgo(iso) {
  const diff = (Date.now()-new Date(iso))/60000;
  if (diff < 1) return t('just_now');
  if (diff < 60) return t('ago_min', Math.round(diff));
  if (diff < 1440) return t('ago_hour', Math.round(diff/60));
  return t('ago_day', Math.round(diff/1440));
}
function displayKey(username) { return username || '?'; }
function getUserColor(username) {
  if (!userColorMap[username]) { userColorMap[username] = USER_COLORS[colorIndex % USER_COLORS.length]; colorIndex++; }
  return userColorMap[username];
}
function esc(s) { return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }

/** Toast the reason the server gave, so a refused save says why instead
 *  of a generic error the user (and the logs) can't act on. */
async function toastError(res) {
  // The service worker answers a write attempted with no network this way.
  if (res.headers.get('X-Offline')) { toast(t('toast_offline')); return; }
  let reason = '';
  try { reason = (await res.json()).error || ''; } catch {}
  toast(reason || t('toast_error'));
}

// ── Day navigation ──
function updateDayNav() {
  localStorage.setItem('logDate', currentDate);
  localStorage.setItem('logDateDay', todayStr());
  document.getElementById('day-label').textContent = fmtDate(currentDate);
  document.getElementById('date-picker').value = currentDate;
  document.getElementById('btn-next').disabled = currentDate >= todayStr();
  renderBirthdayBanner();
}
function changeDay(delta) {
  const d = new Date(currentDate);
  d.setDate(d.getDate() + delta);
  currentDate = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
  updateDayNav();
  loadLog();
  if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
}
function jumpToDate(val) {
  if (!val) return;
  currentDate = val;
  updateDayNav();
  loadLog();
  if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
}
function openDatePicker() {
  const el = document.getElementById('date-picker');
  try {
    if (el.showPicker) el.showPicker();
    else el.focus();
  } catch {
    el.focus();
  }
}

// ── Tab switching ──
function switchTab(name, btn) {
  document.querySelectorAll('.tab-page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  (btn || document.getElementById('tab-btn-'+name)).classList.add('active');
  document.body.classList.toggle('log-active', name === 'log');
  location.hash = name;
  if (name === 'stats') loadStats();
  if (name === 'settings') loadSettings();
}

// ── Babies ──
let babies = [];
let currentBabyId = null;
let baby = { name: '', birthday: '' };

// ── Settings tabs ──
let settingsTab = localStorage.getItem('settingsTab') || 'baby';
let settingsMe = {};
// Bumped after this account's own avatar changes, so the freshly uploaded
// or removed photo shows immediately instead of behind the avatar
// endpoint's 5-minute Cache-Control.
let avatarCacheBust = Date.now();

function avatarHtml(userId, hasAvatar, initialsSource, sizeClass) {
  const cls = 'avatar-circle' + (sizeClass ? ' ' + sizeClass : '');
  if (hasAvatar) {
    return `<img class="${cls}" src="/api/users/${userId}/avatar?v=${avatarCacheBust}" alt="">`;
  }
  return `<div class="${cls}">${esc((initialsSource || '?').charAt(0).toUpperCase())}</div>`;
}
let settingsPasskeys = [];
let settingsTokens = [];

function currentBaby() {
  return babies.find(b => b.id === currentBabyId) || { name: '', birthday: '' };
}

async function loadBabies() {
  try {
    const res = await fetch('/api/babies');
    babies = res.ok ? await res.json() : [];
  } catch {
    babies = [];
  }
  const saved = parseInt(localStorage.getItem('babyId'), 10);
  currentBabyId = babies.some(b => b.id === saved) ? saved : (babies[0]?.id ?? null);
  if (currentBabyId != null) localStorage.setItem('babyId', currentBabyId);
  baby = currentBaby();
  renderBabySwitcherLabel();
}

function renderBabySwitcherLabel() {
  const el = document.getElementById('baby-switcher-btn');
  if (el) el.textContent = currentBaby().name || t('baby_fallback');
}

function switchBaby(id) {
  currentBabyId = id;
  localStorage.setItem('babyId', id);
  baby = currentBaby();
  renderBabySwitcherLabel();
  closeBabySwitcher();
  renderBirthdayBanner();
  loadLog();
  if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
  if (document.getElementById('tab-settings').classList.contains('active')) loadSettings();
}

function openBabySwitcher() {
  document.getElementById('baby-switcher-title').textContent = t('settings_baby_title');
  const list = document.getElementById('baby-switcher-list');
  list.innerHTML = babies.map(b => `
    <div class="quick-opt-btn baby-switch-row${b.id === currentBabyId ? ' selected' : ''}" onclick="switchBaby(${b.id})">${esc(b.name || t('baby_fallback'))}</div>
  `).join('') + `
    <div class="field" style="margin-top:14px;"><input type="text" id="new-baby-name" placeholder="${t('baby_name_placeholder')}"></div>
    <button class="btn" onclick="quickAddBaby()">${t('btn_add_baby')}</button>
  `;
  document.getElementById('baby-overlay').classList.add('open');
}
function closeBabySwitcher() {
  document.getElementById('baby-overlay').classList.remove('open');
}
function babyOverlayClick(e) {
  if (e.target === document.getElementById('baby-overlay')) closeBabySwitcher();
}
async function quickAddBaby() {
  const name = document.getElementById('new-baby-name').value.trim();
  if (!name) return;
  const res = await fetch('/api/babies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (res.ok) {
    const created = await res.json();
    await loadBabies();
    switchBaby(created.id);
    toast(t('toast_saved'));
  } else {
    toast(t('toast_error'));
  }
}

function daysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate();
}

/** Milestone for `dateStr`, or null when that day isn't one. */
function birthdayMilestone(birthday, dateStr) {
  if (!birthday) return null;
  const [by, bm, bd] = birthday.split('-').map(Number);
  const [dy, dm, dd] = dateStr.split('-').map(Number);
  if (!by || !dy) return null;
  if (dateStr < birthday) return null;
  if (dateStr === birthday) return { kind: 'born' };

  // A baby born on the 31st has no 31st in a 30-day month — celebrate on the
  // last day of that month instead.
  const effectiveDay = Math.min(bd, daysInMonth(dy, dm - 1));
  if (dd !== effectiveDay) return null;

  const months = (dy - by) * 12 + (dm - bm);
  if (months <= 0) return null;
  if (months < 12) return { kind: 'months', value: months };
  if (months % 12) return null;
  return { kind: 'years', value: months / 12 };
}

function renderBirthdayBanner() {
  const wrap = document.getElementById('birthday-banner-wrap');
  if (!wrap) return;
  const ms = birthdayMilestone(baby.birthday, currentDate);
  if (!ms) { wrap.innerHTML = ''; return; }

  const who = baby.name || t('baby_fallback');
  let label, headline;
  if (ms.kind === 'born') {
    label = t('bd_welcome');
    headline = t('bd_born_today', who);
  } else if (ms.kind === 'months') {
    label = t('bd_month_label', ms.value);
    headline = t('bd_months_old', { name: who, n: ms.value });
  } else {
    label = t('bd_happy');
    headline = t('bd_years_old', { name: who, n: ms.value });
  }

  wrap.innerHTML = `
    <div class="birthday-banner${ms.kind === 'years' ? ' major' : ''}">
      ${[
        [6,5,8,'#f6ecc9',2.6,0], [16,4,7,'#e8b08f',3.1,0.6], [27,5,5,'#a9c9b7',2.4,1.3],
        [38,4,8,'#e2a0ad',2.9,0.2], [50,5,6,'#f6ecc9',2.7,1.6], [61,4,7,'#a9c9b7',3.3,0.9],
        [72,5,5,'#e8b08f',2.5,1.9], [82,4,8,'#f6ecc9',3.0,0.4], [91,5,6,'#e2a0ad',2.8,1.1],
      ].map(
        ([l, w, h, color, dur, delay]) =>
          `<span class="cf-piece" style="left:${l}%;width:${w}px;height:${h}px;background:${color};animation-duration:${dur}s;animation-delay:${delay}s"></span>`
      ).join('')}
      <div class="bd-icon">${icon('cake')}</div>
      <div class="bd-info">
        <div class="bd-label">${esc(label)}</div>
        <div class="bd-headline">${esc(headline)}</div>
      </div>
    </div>
  `;
}

// ── Sleep banner ──
async function checkOpenSleep() {
  const res = await fetch('/api/sleep/open?baby_id=' + currentBabyId);
  openSleepEntry = res.ok ? await res.json() : null;
  openSleepEntry = pendingOpen('sleep') || openSleepEntry;
  renderSleepBanner();
}
// ── Ambient banner backdrop ──
// Built once per open entry; the 60s tick only rewrites the time text, so
// the animation keeps running instead of restarting every minute.
let sleepBannerTimer = null, walkBannerTimer = null;

function svgBg(inner) {
  return 'url("data:image/svg+xml,' + encodeURIComponent(
    "<svg xmlns='http://www.w3.org/2000/svg' preserveAspectRatio='none' " + inner + '</svg>'
  ) + '")';
}

function buildStarfield(host) {
  let seed = 20260902;
  const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  for (let i = 0; i < 16; i++) {
    const s = document.createElement('span');
    s.className = i % 5 === 2 ? 'bstar spark' : 'bstar';
    // edge-weighted so the middle, behind the text, stays calm
    let x = rnd(); x = x < 0.5 ? x * 0.68 : 0.6 + x * 0.4;
    s.style.left = (x * 100).toFixed(1) + '%';
    s.style.top = (6 + rnd() * 70).toFixed(1) + '%';
    s.style.setProperty('--tw', (3 + rnd() * 4).toFixed(2) + 's');
    s.style.setProperty('--td', (-rnd() * 6).toFixed(2) + 's');
    const sz = (1.8 + rnd() * 2).toFixed(1) + 'px';
    s.style.width = s.style.height = sz;
    host.appendChild(s);
  }
}

function renderSleepBanner() {
  const wrap = document.getElementById('sleep-banner-wrap');
  clearTimeout(sleepBannerTimer);
  if (!openSleepEntry) { wrap.innerHTML = ''; return; }
  const since = fmtTime(openSleepEntry.ts_start);
  const dur = Math.round(durMin(openSleepEntry.ts_start, new Date().toISOString()));
  let banner = wrap.querySelector('.sleep-banner');
  if (!banner || banner.dataset.entry !== String(openSleepEntry.id)) {
    wrap.innerHTML = `
      <div class="sleep-banner" data-entry="${openSleepEntry.id}">
        <div class="banner-decor" aria-hidden="true"><span class="bmoon"><svg viewBox="0 0 24 24"><path d="M20 14.3A8 8 0 1 1 9.7 4a6.3 6.3 0 0 0 10.3 10.3Z"/></svg></span><span class="bshoot"></span></div>
        <div class="sl-body">
          <div class="sl-icon">${icon('sleep')}<span class="sl-dot"></span></div>
          <div class="sl-info">
            <div class="sl-label"></div>
            <div class="sl-since"></div>
          </div>
          <button class="wake-btn" onclick="wakeUp()"></button>
        </div>
      </div>`;
    banner = wrap.querySelector('.sleep-banner');
    buildStarfield(banner.querySelector('.banner-decor'));
  }
  banner.querySelector('.sl-label').textContent = `${t('banner_since')} ${since}`;
  banner.querySelector('.sl-since').textContent = `${fmtDur(dur)} ${t('banner_so_far')}`;
  banner.querySelector('.wake-btn').textContent = t('banner_wakeup');
  sleepBannerTimer = setTimeout(renderSleepBanner, 60000);
}
async function wakeUp() {
  if (!openSleepEntry) return;
  const now = nowUtc();
  if (!closePending(openSleepEntry, now)) {
    await fetch(`/api/entries/${openSleepEntry.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ts_end: now })
    });
  }
  const dur = Math.round(durMin(openSleepEntry.ts_start, now));
  toast(t('toast_wakeup', fmtDur(dur)));
  openSleepEntry = null;
  document.getElementById('sleep-banner-wrap').innerHTML = '';
  loadLog();
}

// ── Walk banner ──
async function checkOpenWalk() {
  const res = await fetch('/api/walk/open?baby_id=' + currentBabyId);
  openWalkEntry = res.ok ? await res.json() : null;
  openWalkEntry = pendingOpen('walk') || openWalkEntry;
  renderWalkBanner();
}
function renderWalkBanner() {
  const wrap = document.getElementById('walk-banner-wrap');
  clearTimeout(walkBannerTimer);
  if (!openWalkEntry) { wrap.innerHTML = ''; return; }
  const since = fmtTime(openWalkEntry.ts_start);
  const dur = Math.round(durMin(openWalkEntry.ts_start, new Date().toISOString()));
  let banner = wrap.querySelector('.sleep-banner');
  if (!banner || banner.dataset.entry !== String(openWalkEntry.id)) {
    wrap.innerHTML = `
      <div class="sleep-banner walk" data-entry="${openWalkEntry.id}">
        <div class="banner-decor" aria-hidden="true"><span class="bsun"></span><span class="pl pl-hills"></span><span class="pl pl-trees"></span></div>
        <div class="sl-body">
          <div class="sl-icon">${icon('walk')}<span class="sl-dot"></span></div>
          <div class="sl-info">
            <div class="sl-label"></div>
            <div class="sl-since"></div>
          </div>
          <button class="wake-btn" onclick="endWalk()"></button>
        </div>
      </div>`;
    banner = wrap.querySelector('.sleep-banner');
    banner.querySelector('.pl-hills').style.backgroundImage = svgBg(
      "viewBox='0 0 260 64'><path fill='#8aa87a' d='M0 64 V45 C26 37 46 35 74 43 C104 51 128 35 160 39 C192 43 214 41 236 37 C246 35 254 36 260 35 V64 Z'/>"
    );
    banner.querySelector('.pl-trees').style.backgroundImage = svgBg(
      "viewBox='0 0 200 64'><g fill='#3d5b33'>" +
      "<path d='M13 53 L26 27 L39 53 Z M23.5 53 h5 V64 h-5 Z'/>" +
      "<path d='M66 55 L78 39 L90 55 Z M75.5 55 h5 V64 h-5 Z'/>" +
      "<path d='M111 54 L124 30 L137 54 Z M121.5 54 h5 V64 h-5 Z'/>" +
      "<path d='M160 56 L172 41 L184 56 Z M169.5 56 h5 V64 h-5 Z'/></g>"
    );
  }
  banner.querySelector('.sl-label').textContent = `${t('banner_walk_since')} ${since}`;
  banner.querySelector('.sl-since').textContent = `${fmtDur(dur)} ${t('banner_walk_so_far')}`;
  banner.querySelector('.wake-btn').textContent = t('tile_walk_end');
  walkBannerTimer = setTimeout(renderWalkBanner, 60000);
}
async function endWalk() {
  if (!openWalkEntry) return;
  const now = nowUtc();
  if (!closePending(openWalkEntry, now)) {
    await fetch(`/api/entries/${openWalkEntry.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ts_end: now })
    });
  }
  const dur = Math.round(durMin(openWalkEntry.ts_start, now));
  toast(t('toast_walk_end', fmtDur(dur)));
  openWalkEntry = null;
  document.getElementById('walk-banner-wrap').innerHTML = '';
  loadLog();
}

// ── Quick actions ──
const QUICK_TYPE_KEYS = ['diaper', 'nursing', 'bottle', 'sleep', 'walk', 'clothing', 'note', 'mood'];

// Lives on the account (see /api/auth/quick-actions), not the browser, so
// it follows the user across devices. Populated by loadQuickActions()
// before the first render; the default covers the gap on a first-ever load.
let quickActionsCache = null;

function getQuickActions() {
  if (Array.isArray(quickActionsCache) && quickActionsCache.length) {
    return quickActionsCache.filter(k => QUICK_TYPE_KEYS.includes(k)).slice(0, 5);
  }
  return ['sleep', 'mood'];
}
async function loadQuickActions() {
  try {
    const me = await (await fetch('/api/auth/me')).json();
    quickActionsCache = me.quick_actions;
    myName = me.name || '';
    showNoteFields = me.show_note_fields !== false;
  } catch {}
}
async function setQuickActions(actions) {
  quickActionsCache = actions.slice(0, 5);
  renderQuickActions();
  await fetch('/api/auth/quick-actions', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quick_actions: quickActionsCache }),
  });
}

function renderQuickActions() {
  const wrap = document.getElementById('quick-actions-wrap');
  if (!wrap) return;
  wrap.innerHTML = getQuickActions().map(key => {
    let label, iconName, tint = '';
    if (key === 'sleep') {
      label = openSleepEntry ? t('banner_wakeup') : t('tile_sleep_start');
      iconName = 'zzz';
      tint = openSleepEntry ? 'tint-sleep' : '';
    } else if (key === 'walk') {
      label = openWalkEntry ? t('tile_walk_end') : t('tile_walk');
      iconName = 'walk';
      tint = openWalkEntry ? 'tint-walk' : '';
    } else {
      const tp = getType(key);
      label = tp.label;
      iconName = tp.icon;
    }
    return `<button class="quick-btn ${tint}" onclick="quickTap('${key}')" title="${esc(label)}">${icon(iconName)}</button>`;
  }).join('');
}

/** Follow a just-logged entry to the day it landed on, so logging at
 *  00:10 (or from a day you were browsing) never files it out of sight. */
function showDayOf(iso) {
  const d = localDate(iso);
  if (d !== currentDate) { currentDate = d; updateDayNav(); }
}

function quickTap(type) {
  if (type === 'sleep') { openSleepEntry ? wakeUp() : quickStartOpen('sleep'); return; }
  if (type === 'walk') { openWalkEntry ? endWalk() : quickStartOpen('walk'); return; }
  if (type === 'clothing') { quickSubmit('clothing'); return; }
  openQuickPopup(type);
}

async function quickStartOpen(type) {
  const now = nowUtc();
  const body = { type, ts_start: now, ts_end: null, note: '', meta: {} };
  const r = await createEntry(body);
  if (r.failed) { await toastError(r.failed); return; }
  const entry = r.saved || { ...body, localId: r.queued.localId, pending: true };
  if (type === 'sleep') openSleepEntry = entry;
  if (type === 'walk') openWalkEntry = entry;
  if (r.saved) toast(t('toast_saved'));
  showDayOf(now);
  loadLog();
}

async function quickSubmit(type, meta = {}, note = '') {
  const now = nowUtc();
  const r = await createEntry({ type, ts_start: now, ts_end: null, note, meta });
  if (r.failed) { await toastError(r.failed); return; }
  if (r.saved) toast(t('toast_saved'));
  closeQuickPopup();
  showDayOf(now);
  loadLog();
}

// <option>s for a bottle's content, with the current baby's default preselected.
function bottleContentOptions() {
  const def = currentBaby().bottle_default_content || 'abgepumpt';
  return ['abgepumpt', 'formula'].map(v =>
    `<option value="${v}"${v === def ? ' selected' : ''}>${t(v === 'abgepumpt' ? 'opt_pumped' : 'opt_formula')}</option>`
  ).join('');
}

function openQuickPopup(type) {
  document.getElementById('quick-title').textContent = getType(type).label;
  const body = document.getElementById('quick-body');
  if (type === 'mood') {
    body.innerHTML = `<div class="quick-opt-row">${['happy', 'neutral', 'fussy', 'crying'].map(m =>
      `<button class="quick-emoji-btn" onclick="quickSubmit('mood',{mood:'${m}'})">${MOOD_EMOJI[m]}</button>`
    ).join('')}</div>`;
  } else if (type === 'diaper') {
    body.innerHTML = `<div class="quick-opt-row">
      <button class="quick-opt-btn" onclick="quickSubmit('diaper',{diaper_type:'nass'})">${t('opt_wet')}</button>
      <button class="quick-opt-btn" onclick="quickSubmit('diaper',{diaper_type:'schmutzig'})">${t('opt_dirty')}</button>
      <button class="quick-opt-btn" onclick="quickSubmit('diaper',{diaper_type:'beides'})">${t('opt_both')}</button>
    </div>`;
  } else if (type === 'nursing') {
    body.innerHTML = `<div class="quick-opt-row">
      <button class="quick-opt-btn" onclick="quickSubmit('nursing',{side:'links'})">${t('opt_left')}</button>
      <button class="quick-opt-btn" onclick="quickSubmit('nursing',{side:'rechts'})">${t('opt_right')}</button>
      <button class="quick-opt-btn" onclick="quickSubmit('nursing',{side:'beide'})">${t('opt_both_sides')}</button>
    </div>`;
  } else if (type === 'bottle') {
    body.innerHTML = `
      <div class="field"><label>${t('lbl_amount')}</label><input type="number" id="q-amount" min="0" step="5" placeholder="120"></div>
      <div class="field"><label>${t('lbl_content')}</label>
        <select id="q-content">${bottleContentOptions()}</select>
      </div>
      <button class="btn" onclick="quickSubmit('bottle',{amount:document.getElementById('q-amount').value,content:document.getElementById('q-content').value})">${t('btn_save')}</button>
    `;
  } else if (type === 'note') {
    body.innerHTML = `
      <div class="field"><textarea id="q-note" rows="3" placeholder="${t('lbl_note')}"></textarea></div>
      <button class="btn" onclick="quickSubmit('note',{},document.getElementById('q-note').value)">${t('btn_save')}</button>
    `;
  }
  document.getElementById('quick-overlay').classList.add('open');
}
function closeQuickPopup() {
  document.getElementById('quick-overlay').classList.remove('open');
}
function quickOverlayClick(e) {
  if (e.target === document.getElementById('quick-overlay')) closeQuickPopup();
}

// ── Log ──
async function loadLog() {
  if (currentBabyId == null) {
    document.getElementById('sleep-banner-wrap').innerHTML = '';
    document.getElementById('walk-banner-wrap').innerHTML = '';
    document.getElementById('quick-actions-wrap').innerHTML = '';
    document.getElementById('entry-list').innerHTML = `<div class="empty">${t('no_baby_yet')}</div>`;
    return;
  }
  await checkOpenSleep();
  await checkOpenWalk();
  renderQuickActions();
  const allRes = await fetch(`/api/entries?limit=500&baby_id=${currentBabyId}`);
  const allEntries = await allRes.json();
  userColorMap = {}; colorIndex = 0;
  allEntries.forEach(e => getUserColor(displayKey(e.username)));

  const res = await fetch(`/api/entries?date=${currentDate}&baby_id=${currentBabyId}`);
  // Entries still waiting to be sent belong in the day they were logged
  // into, or tapping a quick action offline would look like it did nothing.
  const entries = [...pendingForDay(currentDate, currentBabyId), ...(await res.json())]
    .sort((a, b) => (a.ts_start < b.ts_start ? 1 : -1));
  currentEntries = entries;

  const todayKeys = [...new Set(entries.map(e => displayKey(e.username)))];
  const legend = document.getElementById('ip-legend');
  legend.innerHTML = todayKeys.map(key => `
    <div class="ip-legend-item">
      <div class="ip-dot" style="background:${getUserColor(key)}"></div>${esc(key)}
    </div>
  `).join('');

  const diaperEntries = entries.filter(e => e.type === 'diaper');
  const pooCount = diaperEntries.filter(e => ['schmutzig','beides','dirty','both'].includes(e.meta?.diaper_type)).length;
  const feedingMl = entries.filter(e => e.type === 'bottle').reduce((sum, e) => sum + (Number(e.meta?.amount) || 0), 0);
  const chip = (iconName, label) => `<div class="count-chip">${icon(iconName)}<span>${esc(label)}</span></div>`;
  const chips = [];
  if (diaperEntries.length) chips.push(chip('diaper', t('diaper_count', diaperEntries.length)));
  if (pooCount) chips.push(chip('diaper', t('diaper_poo_count', pooCount)));
  if (feedingMl) chips.push(chip('bottle', t('feeding_ml', feedingMl)));
  document.getElementById('diaper-count').innerHTML = chips.join('');

  const list = document.getElementById('entry-list');
  if (!entries.length) {
    list.innerHTML = `<div class="empty">${t('no_entries')}</div>`;
    if (logView === 'timeline') renderTimeline();
    return;
  }

  list.innerHTML = entries.map(e => {
    const color = getUserColor(displayKey(e.username));
    const tp = getType(e.type);
    const m = e.meta || {};
    let timeStr = fmtTime(e.ts_start);
    let metaStr = '';

    if (e.type === 'sleep') {
      if (e.ts_end) {
        const dur = Math.round(durMin(e.ts_start, e.ts_end));
        timeStr = `${fmtStartTime(e.ts_start)} – ${fmtTime(e.ts_end)}`;
        metaStr = fmtDur(dur);
      } else {
        timeStr = `${fmtStartTime(e.ts_start)} – ${t('still_sleeping')}`;
      }
    }
    if (e.type === 'diaper' && m.diaper_type) metaStr = tMeta(m.diaper_type);
    if (e.type === 'nursing') {
      if (e.ts_end) timeStr = `${fmtStartTime(e.ts_start)} – ${fmtTime(e.ts_end)}`;
      if (m.side) metaStr = tMeta(m.side);
    }
    if (e.type === 'bottle' && m.amount) metaStr = `${m.amount} ml`;
    if (e.type === 'weight') {
      const parts = [];
      if (m.weight) parts.push(`${m.weight} g`);
      if (m.height) parts.push(`${m.height} cm`);
      if (parts.length) metaStr = parts.join(' · ');
    }
    if (e.type === 'mood' && m.mood) metaStr = tMeta(m.mood);
    if (e.type === 'walk') {
      if (e.ts_end) {
        const dur = Math.round(durMin(e.ts_start, e.ts_end));
        timeStr = `${fmtStartTime(e.ts_start)} – ${fmtTime(e.ts_end)}`;
        metaStr = fmtDur(dur);
      } else {
        timeStr = `${fmtStartTime(e.ts_start)} – ${t('still_walking')}`;
      }
    }

    const moodKey = `mood_${m.mood}`;
    const iconHtml = e.type === 'mood'
      ? icon(moodKey in ICONS ? moodKey : 'mood')
      : typeIcon(tp.icon);

    // A queued entry has no server id yet, so it can't be edited — only
    // dropped again before it is sent.
    const remove = e.pending
      ? `dropPending('${e.localId}')`
      : `deleteEntry(${e.id})`;
    return `
      <div class="entry-item${e.pending ? ' pending' : ''}"${e.pending ? '' : ` onclick="openEditModal(${e.id})"`}>
        <div class="entry-icon tint-${typeTint(e.type)}">${iconHtml}</div>
        <div class="entry-body">
          <div class="entry-type">${tp.label}${e.pending ? ` · ${t('pending_tag')}` : ''}</div>
          <div class="entry-time">${timeStr}</div>
          ${metaStr ? `<div class="entry-meta">${esc(metaStr)}</div>` : ''}
          ${e.note ? `<div class="entry-note">${esc(e.note)}</div>` : ''}
        </div>
        <span class="ip-badge" style="background:${color}" title="${esc(e.username || '')}"></span>
        <button class="del-btn" onclick="event.stopPropagation(); ${remove}" title="${t('confirm_delete')}"><svg viewBox="0 0 24 24" class="ic"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
      </div>
    `;
  }).join('');
  if (logView === 'timeline') renderTimeline();
}

async function deleteEntry(id) {
  if (!confirm(t('confirm_delete'))) return;
  await fetch('/api/entries/'+id, { method: 'DELETE' });
  toast(t('toast_deleted'));
  loadLog();
}

// ── Timeline ──
let logView = localStorage.getItem('logView') || 'list';
function setLogView(view) {
  logView = view;
  localStorage.setItem('logView', view);
  document.querySelectorAll('#log-view-toggle .range-pill').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  document.getElementById('log-list-view').style.display = view === 'list' ? '' : 'none';
  document.getElementById('timeline-view').style.display = view === 'timeline' ? '' : 'none';
  renderTimelineLegend(view === 'timeline');
  if (view === 'timeline') renderTimeline();
}

function dayMinutes(iso) {
  const d = localDate(iso);
  if (d < currentDate) return 0;
  if (d > currentDate) return 1440;
  return localMinutes(iso);
}
function spanEndMinutes(e, nowMin) {
  if (e.ts_end) return dayMinutes(e.ts_end);
  return nowMin != null ? nowMin : 1440;
}

const MOOD_EMOJI = { happy: '😊', neutral: '😐', fussy: '😕', crying: '😢' };

// Stretches at the edges of the day holding nothing but sleep get squeezed to
// this fraction of the normal scale, so a long night doesn't push the busy
// hours off-screen. Anything shorter than the threshold is left alone.
const TL_SQUEEZE = 0.22;
const TL_SQUEEZE_MIN = 150;

/**
 * Piecewise minute -> pixel scale for one day.
 *
 * Returns `at(minute)`, the total `size`, and the squeezed ranges so the grid
 * can mark them.
 */
function makeTimeScale(entries, pxPerHour, nowMin) {
  const per = pxPerHour / 60;

  // Anchors are the moments worth showing at full scale. Sleep is excluded:
  // squeezing it is the whole point. With nothing but sleep, fall back to the
  // sleep spans so the day still has something to frame.
  // An entry without ts_end is a point in time, not something running until
  // the end of the day — anchoring on spanEndMinutes here would peg the tail
  // to 24:00 and defeat the squeeze. Ongoing spans are covered by the `now`
  // anchor below.
  const anchor = (e) => [
    dayMinutes(e.ts_start),
    e.ts_end ? dayMinutes(e.ts_end) : dayMinutes(e.ts_start),
  ];

  const spans = [];
  entries.forEach(e => {
    if (e.type === 'sleep') return;
    spans.push(anchor(e));
  });
  if (!spans.length) entries.forEach(e => spans.push(anchor(e)));
  if (nowMin != null) spans.push([nowMin, nowMin]);

  let head = 0;
  let tail = 1440;
  if (spans.length) {
    const first = Math.min(...spans.map(s => s[0]));
    const last = Math.max(...spans.map(s => s[1]));
    // Keep a whole hour of context on each side of the busy stretch.
    head = Math.max(0, Math.floor(first / 60) * 60 - 60);
    tail = Math.min(1440, Math.ceil(last / 60) * 60 + 60);
  }
  if (head < TL_SQUEEZE_MIN) head = 0;
  if (1440 - tail < TL_SQUEEZE_MIN) tail = 1440;

  const headPx = head * per * TL_SQUEEZE;
  const bodyPx = (tail - head) * per;
  const tailPx = (1440 - tail) * per * TL_SQUEEZE;

  const at = (min) => {
    const m = Math.max(0, Math.min(1440, min));
    if (m <= head) return m * per * TL_SQUEEZE;
    if (m <= tail) return headPx + (m - head) * per;
    return headPx + bodyPx + (m - tail) * per * TL_SQUEEZE;
  };

  return {
    at,
    size: headPx + bodyPx + tailPx,
    head,
    tail,
    squeezed: head > 0 || tail < 1440,
    isSqueezed: (min) => min < head || min > tail,
  };
}

/** Feed/diaper/mood key, shown beside the view toggle while the timeline is up. */
function renderTimelineLegend(show) {
  const slot = document.getElementById('tl-legend-slot');
  if (!slot) return;
  slot.innerHTML = show ? `
    <div class="tl-legend-item"><span class="tl-legend-swatch" style="background:var(--feed);"></span><span class="lbl" style="font-size:9px;color:var(--feed);">${t('types').feeding}</span></div>
    <div class="tl-legend-item"><span class="tl-legend-swatch" style="background:var(--accent);"></span><span class="lbl" style="font-size:9px;color:var(--accent-ink);">${t('types').diaper}</span></div>
    <div class="tl-legend-item"><span style="font-size:12px;line-height:1;">${MOOD_EMOJI.happy}</span><span class="lbl" style="font-size:9px;color:var(--mood);">${t('types').mood}</span></div>` : '';
}

function renderTimeline() {
  const wrap = document.getElementById('timeline-view');
  if (!wrap) return;
  renderTimelineLegend(true);
  const entries = currentEntries;
  const sleeps = entries.filter(e => e.type === 'sleep');
  const walks = entries.filter(e => e.type === 'walk');
  const feeds = entries.filter(e => e.type === 'nursing' || e.type === 'bottle');
  const diapers = entries.filter(e => e.type === 'diaper');
  const moods = entries.filter(e => e.type === 'mood');
  const isToday = currentDate === todayStr();
  const now = new Date();
  const nowMin = isToday ? now.getHours() * 60 + now.getMinutes() : null;

  const wide = window.matchMedia('(min-width: 640px)').matches;
  const gridW = Math.max(wrap.clientWidth - 40 - 30, 240);
  const scale = makeTimeScale(entries, wide ? 28 : 30, nowMin);
  wrap.innerHTML = wide
    ? renderTimelineWide(sleeps, walks, feeds, diapers, moods, nowMin, scale)
    : renderTimelineNarrow(sleeps, walks, feeds, diapers, moods, nowMin, gridW, scale);
}

function renderTimelineNarrow(sleeps, walks, feeds, diapers, moods, nowMin, gridW, scale) {
  const px = 30, gridH = scale.size, barW = 56;
  const moodColW = moods.length ? 24 : 0, laneW = (gridW - moodColW) / 2, totalW = laneW * 2 + moodColW;
  const sleepLeft = (laneW - barW) / 2, walkLeft = laneW + (laneW - barW) / 2;

  let bars = '';
  sleeps.forEach(e => {
    const top = scale.at(dayMinutes(e.ts_start));
    const h = Math.max(scale.at(spanEndMinutes(e, nowMin)) - top, 4);
    bars += `<div style="position:absolute;left:${sleepLeft}px;top:${top}px;width:${barW}px;height:${h}px;background:var(--sleep-soft);border:1.5px solid var(--sleep);border-radius:8px;cursor:pointer;" onclick="openEditModal(${e.id})"></div>`;
  });
  walks.forEach(e => {
    const top = scale.at(dayMinutes(e.ts_start));
    const h = Math.max(scale.at(spanEndMinutes(e, nowMin)) - top, 4);
    bars += `<div style="position:absolute;left:${walkLeft}px;top:${top}px;width:${barW}px;height:${h}px;background:var(--walk-soft);border:1.5px solid var(--walk);border-radius:8px;cursor:pointer;" onclick="openEditModal(${e.id})"></div>`;
  });

  let lines = '';
  feeds.forEach(e => {
    const center = scale.at(dayMinutes(e.ts_start));
    lines += `<div style="position:absolute;left:0px;top:${center-8}px;width:${laneW*2}px;height:16px;cursor:pointer;" onclick="openEditModal(${e.id})">
      <div style="position:absolute;left:0;top:6px;width:100%;height:4px;background:rgba(160,90,114,0.35);border-top:1px solid var(--feed);border-bottom:1px solid var(--feed);"></div>
    </div>`;
  });
  diapers.forEach(e => {
    const center = scale.at(dayMinutes(e.ts_start));
    lines += `<div style="position:absolute;left:0px;top:${center-8}px;width:${laneW*2}px;height:16px;cursor:pointer;" onclick="openEditModal(${e.id})">
      <div style="position:absolute;left:0;top:6px;width:100%;height:4px;background:rgba(184,134,58,0.35);border-top:1px solid var(--accent);border-bottom:1px solid var(--accent);"></div>
    </div>`;
  });

  let moodMarks = '';
  moods.forEach(e => {
    const center = scale.at(dayMinutes(e.ts_start));
    const emoji = MOOD_EMOJI[e.meta?.mood] || MOOD_EMOJI.neutral;
    moodMarks += `<div style="position:absolute;left:${laneW*2}px;top:${center-10}px;width:${moodColW}px;height:20px;display:flex;align-items:center;justify-content:center;font-size:15px;line-height:1;cursor:pointer;" onclick="openEditModal(${e.id})">${emoji}</div>`;
  });

  let hours = '';
  if (scale.head > 0) {
    hours += `<div class="tl-squeezed" style="left:0;top:0;width:${totalW}px;height:${scale.at(scale.head)}px;"></div>`;
  }
  if (scale.tail < 1440) {
    const top = scale.at(scale.tail);
    hours += `<div class="tl-squeezed" style="left:0;top:${top}px;width:${totalW}px;height:${scale.size - top}px;"></div>`;
  }
  for (let h = 0; h <= 24; h++) {
    const min = h * 60;
    const top = scale.at(min);
    const squeezed = scale.isSqueezed(min);
    // Inside a squeezed stretch the hour lines would collide, so only the
    // boundary hours are drawn there.
    const edge = min === scale.head || min === scale.tail;
    if (!squeezed || edge || h === 0 || h === 24) {
      hours += `<div style="position:absolute;left:0;top:${top}px;width:${totalW}px;height:1px;background:var(--border);"></div>`;
    }
    if ((!squeezed && h % 3 === 0) || edge || h === 0 || h === 24) {
      hours += `<div style="position:absolute;left:-30px;top:${top-5}px;width:26px;text-align:right;font-family:var(--tl-mono);font-size:9px;color:var(--ink2);">${pad(h)}</div>`;
    }
  }

  let nowLine = '';
  if (nowMin != null) {
    const top = scale.at(nowMin);
    nowLine = `
      <div style="position:absolute;left:-30px;top:${top}px;width:${totalW+30}px;height:0;border-top:1.5px dashed var(--accent-ink);z-index:5;"></div>
      <div style="position:absolute;left:-30px;top:${top-11}px;background:var(--accent-ink);color:#fff;font-family:var(--tl-mono);font-size:8px;letter-spacing:0.05em;padding:2px 4px;border-radius:4px;z-index:5;">${t('tl_now')}</div>`;
  }

  return `
    <div class="timeline-wrap" style="--tl-mono:ui-monospace,'Cascadia Code','Source Code Pro',monospace;">
      <div style="position:relative;">
        <div style="display:flex;margin-left:30px;margin-bottom:4px;">
          <div class="tl-lane-header" style="width:${laneW}px;color:var(--sleep);">${icon('sleep')}<span class="lbl" style="font-size:10px;">${t('types').sleep}</span></div>
          <div class="tl-lane-header" style="width:${laneW}px;color:var(--walk);">${icon('walk')}<span class="lbl" style="font-size:10px;">${t('types').walk}</span></div>
        </div>
        <div style="position:relative;height:${gridH}px;margin-left:30px;">
          <div style="position:absolute;left:${laneW}px;top:0;width:1px;height:${gridH}px;background:var(--border);"></div>
          ${moodColW ? `<div style="position:absolute;left:${laneW*2}px;top:0;width:1px;height:${gridH}px;background:var(--border);"></div>` : ''}
          ${hours}${lines}${bars}${moodMarks}${nowLine}
        </div>
      </div>
    </div>
  `;
}

function renderTimelineWide(sleeps, walks, feeds, diapers, moods, nowMin, scale) {
  const trackW = scale.size, rowH = 80, barH = 40;

  let bars = '';
  sleeps.forEach(e => {
    const left = scale.at(dayMinutes(e.ts_start));
    const w = Math.max(scale.at(spanEndMinutes(e, nowMin)) - left, 4);
    bars += `<div style="position:absolute;left:${left}px;top:20px;width:${w}px;height:${barH}px;background:var(--sleep-soft);border:1.5px solid var(--sleep);border-radius:8px;cursor:pointer;" onclick="openEditModal(${e.id})"></div>`;
  });
  walks.forEach(e => {
    const left = scale.at(dayMinutes(e.ts_start));
    const w = Math.max(scale.at(spanEndMinutes(e, nowMin)) - left, 4);
    bars += `<div style="position:absolute;left:${left}px;top:${rowH+20}px;width:${w}px;height:${barH}px;background:var(--walk-soft);border:1.5px solid var(--walk);border-radius:8px;cursor:pointer;" onclick="openEditModal(${e.id})"></div>`;
  });

  let lines = '';
  feeds.forEach(e => {
    const center = scale.at(dayMinutes(e.ts_start));
    lines += `<div style="position:absolute;left:${center-8}px;top:0;width:16px;height:${rowH*2}px;cursor:pointer;" onclick="openEditModal(${e.id})">
      <div style="position:absolute;left:6px;top:0;width:4px;height:100%;background:rgba(160,90,114,0.35);border-left:1px solid var(--feed);border-right:1px solid var(--feed);"></div>
    </div>`;
  });
  diapers.forEach(e => {
    const center = scale.at(dayMinutes(e.ts_start));
    lines += `<div style="position:absolute;left:${center-8}px;top:0;width:16px;height:${rowH*2}px;cursor:pointer;" onclick="openEditModal(${e.id})">
      <div style="position:absolute;left:6px;top:0;width:4px;height:100%;background:rgba(184,134,58,0.35);border-left:1px solid var(--accent);border-right:1px solid var(--accent);"></div>
    </div>`;
  });

  let moodMarks = '';
  moods.forEach(e => {
    const center = scale.at(dayMinutes(e.ts_start));
    const emoji = MOOD_EMOJI[e.meta?.mood] || MOOD_EMOJI.neutral;
    moodMarks += `<div style="position:absolute;left:${center-10}px;top:0;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:15px;line-height:1;cursor:pointer;" onclick="openEditModal(${e.id})">${emoji}</div>`;
  });

  let bands = '';
  if (scale.head > 0) {
    bands += `<div class="tl-squeezed" style="left:0;top:0;width:${scale.at(scale.head)}px;height:${rowH*2}px;"></div>`;
  }
  if (scale.tail < 1440) {
    const left = scale.at(scale.tail);
    bands += `<div class="tl-squeezed" style="left:${left}px;top:0;width:${scale.size - left}px;height:${rowH*2}px;"></div>`;
  }

  let hours = '';
  for (let h = 0; h <= 24; h++) {
    const min = h * 60;
    const left = scale.at(min);
    const squeezed = scale.isSqueezed(min);
    const edge = min === scale.head || min === scale.tail;
    if ((!squeezed && h % 3 === 0) || edge || h === 0 || h === 24) {
      hours += `<div style="position:absolute;left:${left}px;top:0;width:1px;height:${rowH*2}px;background:var(--border);"></div>`;
      hours += `<span style="position:absolute;left:${left}px;top:0;font-family:var(--tl-mono);font-size:10px;color:var(--ink2);">${pad(h)}</span>`;
    }
  }

  let nowLine = '';
  if (nowMin != null) {
    const left = scale.at(nowMin);
    nowLine = `
      <div style="position:absolute;left:${left}px;top:-4px;width:0;height:${rowH*2+8}px;border-left:1.5px dashed var(--accent-ink);z-index:5;"></div>
      <div style="position:absolute;left:${left-19}px;top:-18px;background:var(--accent-ink);color:#fff;font-family:var(--tl-mono);font-size:8px;letter-spacing:0.05em;padding:2px 4px;border-radius:4px;z-index:5;">${t('tl_now')}</div>`;
  }

  return `
    <div class="timeline-wrap" style="--tl-mono:ui-monospace,'Cascadia Code','Source Code Pro',monospace;">
      <div style="position:relative;margin-left:70px;">
        <div style="position:relative;height:18px;margin-bottom:8px;">${hours}</div>
        <div style="position:relative;width:${trackW}px;height:${rowH*2}px;">
          ${bands}
          <div style="position:absolute;left:0;top:${rowH}px;width:${trackW}px;height:1px;background:var(--border);"></div>
          <div style="position:absolute;left:-70px;top:0;width:62px;height:${rowH}px;display:flex;align-items:center;gap:5px;color:var(--sleep);">${icon('sleep')}<span class="lbl" style="font-size:10px;">${t('types').sleep}</span></div>
          <div style="position:absolute;left:-70px;top:${rowH}px;width:62px;height:${rowH}px;display:flex;align-items:center;gap:5px;color:var(--walk);">${icon('walk')}<span class="lbl" style="font-size:10px;">${t('types').walk}</span></div>
          ${lines}${bars}${nowLine}
        </div>
        <div style="position:relative;width:${trackW}px;height:20px;margin-top:2px;">${moodMarks}</div>
      </div>
    </div>
  `;
}

function growthChart(points, label, unit, colorKey) {
  const W = 100, H = 40, pad = 3;
  const xs = points.map(p => new Date(p.x).getTime());
  const ys = points.map(p => p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs), spanX = (maxX - minX) || 1;
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const yMargin = (maxY - minY) * 0.15 || 1;
  const yMin = minY - yMargin, yMax = maxY + yMargin, spanY = yMax - yMin;

  const px = x => pad + ((x - minX) / spanX) * (W - pad * 2);
  const py = y => H - pad - ((y - yMin) / spanY) * (H - pad * 2);

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${px(new Date(p.x).getTime()).toFixed(1)},${py(p.y).toFixed(1)}`).join(' ');
  const dots = points.map(p => `<circle cx="${px(new Date(p.x).getTime()).toFixed(1)}" cy="${py(p.y).toFixed(1)}" r="1.6" fill="var(--${colorKey})"/>`).join('');
  const first = points[0], last = points[points.length - 1];
  const shortDate = iso => `${iso.slice(8,10)}.${iso.slice(5,7)}.`;

  return `
    <div class="growth-chart">
      <div class="growth-chart-head">
        <span class="growth-chart-label" style="color:var(--${colorKey})">${label}</span>
        <span class="growth-chart-val">${last.y} ${unit}</span>
      </div>
      <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" class="growth-svg">
        <path d="${pathD}" fill="none" stroke="var(--${colorKey})" stroke-width="1.4" vector-effect="non-scaling-stroke"/>
        ${dots}
      </svg>
      <div class="growth-chart-range"><span>${shortDate(first.x)}</span><span>${shortDate(last.x)}</span></div>
    </div>`;
}

// ── Stats ──
async function loadStats(fromTimer = false) {
  if (currentBabyId == null) {
    document.getElementById('stats-content').innerHTML = `<div class="empty">${t('no_baby_yet')}</div>`;
    document.getElementById('rhythm-content').innerHTML = '';
    return;
  }
  const res = await fetch(`/api/stats?date=${currentDate}&baby_id=${currentBabyId}`);
  const data = await res.json();
  const el = document.getElementById('stats-content');

  const lastTypes = ['diaper','feeding','sleep','walk','weight'];
  let lastCards = '';
  lastTypes.forEach(key => {
    const e = data.last[key];
    if (!e) return;
    const tp = getType(key);
    let valStr = fmtAgo(e.ts_start);
    let sub = fmtTime(e.ts_start);
    if (key === 'sleep') {
      if (e.ts_end) {
        valStr = `${t('stat_awake_since')} ${fmtDur(Math.round(durMin(e.ts_end, new Date().toISOString())))}`;
        sub = fmtTime(e.ts_end);
      } else {
        valStr = `${t('stat_asleep_since')} ${fmtDur(Math.round(durMin(e.ts_start, new Date().toISOString())))}`;
      }
    }
    if (key === 'walk') {
      if (e.ts_end) {
        valStr = `${t('stat_back_since')} ${fmtDur(Math.round(durMin(e.ts_end, new Date().toISOString())))}`;
        sub = fmtTime(e.ts_end);
      } else {
        valStr = `${t('stat_walking_since')} ${fmtDur(Math.round(durMin(e.ts_start, new Date().toISOString())))}`;
      }
    }
    if (key === 'weight' && (e.meta?.weight || e.meta?.height)) {
      const parts = [];
      if (e.meta.weight) parts.push(e.meta.weight + ' g');
      if (e.meta.height) parts.push(e.meta.height + ' cm');
      valStr = parts.join(' · ');
      sub = fmtAgo(e.ts_start);
    }
    const active = (key === 'sleep' || key === 'walk') && !e.ts_end;
    lastCards += `
      <div class="stat-card${active ? ' tint-'+key : ''}">
        <div class="s-label">${typeIcon(tp.icon)}${tp.label}</div>
        <div class="s-val" style="font-size:1rem;padding-top:2px">${valStr}</div>
        <div class="s-sub">${sub}</div>
      </div>`;
  });

  let ivCards = '';
  ['diaper','feeding'].forEach(key => {
    const iv = data.intervals[key];
    if (!iv) return;
    const tp = getType(key);
    ivCards += `
      <div class="stat-card">
        <div class="s-label">${typeIcon(tp.icon)}${tp.label} · ${t('stat_interval')}</div>
        <div class="s-val">${fmtDur(iv.last)}</div>
        <div class="s-sub">${t('stat_avg')}: ${fmtDur(iv.avg)}</div>
      </div>`;
  });
  if (data.avg_sleep_min != null) {
    ivCards += `
      <div class="stat-card">
        <div class="s-label">${typeIcon(getType('sleep').icon)}${t('stat_avg_sleep')}</div>
        <div class="s-val">${fmtDur(data.avg_sleep_min)}</div>
      </div>`;
  }
  if (data.avg_awake_min != null) {
    ivCards += `
      <div class="stat-card">
        <div class="s-label">${typeIcon(getType('sleep').icon)}${t('stat_avg_awake')}</div>
        <div class="s-val">${fmtDur(data.avg_awake_min)}</div>
      </div>`;
  }

  let sleepBars = `<div class="empty">${t('no_sleep_data')}</div>`;
  if (data.sleep_durations.length) {
    const max = Math.max(...data.sleep_durations.map(s => s.minutes));
    sleepBars = data.sleep_durations.map(s => `
      <div class="sleep-row">
        <span class="sleep-time">${fmtTime(s.start)}&thinsp;–&thinsp;${fmtTime(s.end)}</span>
        <div class="sleep-bar-bg"><div class="sleep-bar" style="width:${Math.round(s.minutes/max*100)}%"></div></div>
        <span class="sleep-dur">${fmtDur(s.minutes)}</span>
      </div>`).join('');
  }

  const weightPoints = data.growth.filter(g => g.weight).map(g => ({ x: g.time, y: parseFloat(g.weight) }));
  const heightPoints = data.growth.filter(g => g.height).map(g => ({ x: g.time, y: parseFloat(g.height) }));
  let growthCharts = `<div class="empty">${t('no_growth_data')}</div>`;
  if (weightPoints.length || heightPoints.length) {
    growthCharts = '';
    if (weightPoints.length) growthCharts += growthChart(weightPoints, t('growth_weight'), 'g', 'accent');
    if (heightPoints.length) growthCharts += growthChart(heightPoints, t('growth_height'), 'cm', 'sleep');
  }

  el.innerHTML = `
    <div class="section-title">${t('section_last')}</div>
    <div class="stats-grid">${lastCards||`<div class="empty">${t('no_data')}</div>`}</div>
    <div class="section-title">${t('section_intervals')}</div>
    <div class="stats-grid">${ivCards||`<div class="empty">${t('not_enough_data')}</div>`}</div>
    <div class="section-title with-action"><span>${t('section_growth')}</span><button class="btn-tiny" onclick="openMeasurementModal()">${t('btn_add_measurement')}</button></div>
    ${growthCharts}
    <div class="section-title">${t('section_sleep')}</div>
    ${sleepBars}
  `;

  if (!fromTimer) loadRhythm();
  if (document.getElementById('tab-stats').classList.contains('active')) setTimeout(() => loadStats(true), 60000);
}

// Typical sleep windows and bottle-feed slots, learned from history.
// Its own container so the 60s stats re-render doesn't wipe it.
async function loadRhythm() {
  const el = document.getElementById('rhythm-content');
  if (!el || currentBabyId == null) { if (el) el.innerHTML = ''; return; }
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
  let r;
  try {
    const res = await fetch(`/api/rhythm?baby_id=${currentBabyId}&tz=${encodeURIComponent(tz)}`);
    if (!res.ok) { el.innerHTML = ''; return; }
    r = await res.json();
  } catch { el.innerHTML = ''; return; }

  const tracked = `${r.days_analyzed}/${r.days_analyzed + r.days_skipped} ${t('rhythm_days_label')}`;
  if (r.days_analyzed < 4) {
    el.innerHTML = `<div class="section-title">${t('section_rhythm')}</div>
      <div class="empty">${t('rhythm_not_enough')} (${tracked})</div>`;
    return;
  }

  const toMin = s => { const [h, m] = s.split(':').map(Number); return h * 60 + m; };
  const seg = (a, b) => `<div class="rh-sleep" style="left:${a / 1440 * 100}%;width:${(b - a) / 1440 * 100}%"></div>`;
  let bars = '';
  r.sleep.forEach(w => {
    const a = toMin(w.start), b = toMin(w.end);
    bars += b <= a ? seg(a, 1440) + seg(0, b) : seg(a, b);
  });
  const ticks = [0, 6, 12, 18].map(h =>
    `<span class="rh-tick" style="left:${h / 24 * 100}%">${String(h).padStart(2, '0')}</span>`).join('');
  const sleepBlock = r.sleep.length
    ? `<div class="rh-strip">${ticks}<div class="rh-track">${bars}</div></div>`
    : `<div class="empty">${t('rhythm_no_sleep')}</div>`;

  const feeds = r.feeds.length
    ? r.feeds.map(f => `
        <div class="rh-feed">
          <span class="rh-feed-time">${f.time}</span>
          <span class="rh-feed-ml">~${f.ml}${f.ml_low !== f.ml_high ? ` <span class="rh-feed-range">(${f.ml_low}–${f.ml_high})</span>` : ''} ml</span>
          <span class="rh-feed-days" title="${t('rhythm_days_label')}">${f.days}×</span>
        </div>`).join('')
    : `<div class="empty">${t('rhythm_no_feeds')}</div>`;

  el.innerHTML = `
    <div class="section-title">${t('section_rhythm')}</div>
    <div class="field-hint" style="margin:-4px 0 12px;">${t('rhythm_hint')} · ${tracked}</div>
    <div class="rh-sub">${t('types').sleep}</div>
    ${sleepBlock}
    <div class="rh-sub" style="margin-top:16px;">${t('tile_bottle')}</div>
    <div class="rh-feeds">${feeds}</div>
  `;
}

// ── Settings ──
async function loadSettings() {
  const [meRes, passkeysRes, tokensRes] = await Promise.all([
    fetch('/api/auth/me'),
    fetch('/api/auth/passkeys'),
    fetch('/api/auth/tokens'),
  ]);
  settingsMe = await meRes.json();
  quickActionsCache = settingsMe.quick_actions;
  settingsPasskeys = await passkeysRes.json();
  settingsTokens = await tokensRes.json();
  renderSettingsTabs();
  renderSettingsTab();
}

function switchSettingsTab(tabName) {
  settingsTab = tabName;
  localStorage.setItem('settingsTab', tabName);
  renderSettingsTabs();
  renderSettingsTab();
}

function renderSettingsTabs() {
  const el = document.getElementById('settings-tabs');
  if (!el) return;
  const tabs = [
    ['baby', t('settings_tab_baby')],
    ['quicklog', t('settings_tab_quicklog')],
    ['account', t('settings_tab_account')],
  ];
  if (settingsMe.is_admin) tabs.push(['admin', t('settings_tab_admin')]);
  el.innerHTML = tabs.map(([key, label]) =>
    `<button class="settings-tab${settingsTab === key ? ' active' : ''}" onclick="switchSettingsTab('${key}')">${esc(label)}</button>`
  ).join('');
}

function renderSettingsTab() {
  if (settingsTab === 'quicklog') renderQuickLogTab();
  else if (settingsTab === 'account') renderAccountTab();
  else if (settingsTab === 'admin' && settingsMe.is_admin) {
    settingsMe.totp_enabled ? loadAdminTab() : renderAdminTotpRequired();
  }
  else renderBabyTab();
}

// ── Admin ──
function renderAdminTotpRequired() {
  document.getElementById('settings-tab-content').innerHTML = `
    <div class="settings-card">
      <div class="settings-card-title">${icon('shield')}${t('lbl_admin_totp_required_title')}</div>
      <div style="font-size:0.85rem;color:var(--ink2);line-height:1.5;margin-bottom:14px;">${t('lbl_admin_totp_required_body')}</div>
      <button class="btn-small" onclick="switchSettingsTab('account')">${t('settings_tab_account')}</button>
    </div>
  `;
}

async function loadAdminTab() {
  const el = document.getElementById('settings-tab-content');
  el.innerHTML = `<div class="empty">${t('loading')}</div>`;
  const [usersRes, babiesRes, invitesRes] = await Promise.all([
    fetch('/api/admin/users'),
    fetch('/api/admin/babies'),
    fetch('/api/admin/invites'),
  ]);
  if (!usersRes.ok || !babiesRes.ok || !invitesRes.ok) { el.innerHTML = `<div class="empty">${t('toast_error')}</div>`; return; }
  renderAdminTab(await usersRes.json(), await babiesRes.json(), await invitesRes.json());
}

function renderAdminTab(users, babies, invites) {
  const el = document.getElementById('settings-tab-content');
  el.innerHTML = `
    <div class="settings-card">
      <div class="settings-card-title">${t('lbl_admin_invites')}</div>
      <div style="font-size:0.78rem;color:var(--ink2);margin-bottom:14px;line-height:1.4;">${t('lbl_invite_hint')}</div>
      <div class="field"><label>${t('lbl_invite_email_optional')}</label>
        <input type="email" id="new-invite-email" placeholder="name@example.com">
      </div>
      <div class="baby-actions" style="margin-bottom:0;">
        <button class="btn-small" onclick="adminCreateInvite()">${t('btn_create_invite')}</button>
      </div>
      <div id="new-invite-result"></div>
      ${invites.length ? '<div style="margin-top:14px;padding-top:14px;border-top:1px dashed var(--border);"></div>' : ''}
      ${invites.map(i => `
        <div class="security-row">
          <div>
            <div class="s-name">${esc(i.email || t('lbl_invite_anyone'))}</div>
            <div class="s-sub">${i.used_at ? `${t('lbl_invite_used')} ${esc(i.used_at.slice(0, 10))}` : `${t('lbl_invite_expires')} ${esc(i.expires_at.slice(0, 10))}`}</div>
          </div>
          ${i.used_at ? `<span class="badge-role viewer">${t('lbl_invite_used')}</span>` : `<button class="btn-small secondary" onclick="adminRevokeInvite(${i.id})">${t('btn_revoke')}</button>`}
        </div>
      `).join('') || `<div class="empty">${t('lbl_none')}</div>`}
    </div>
    <div class="settings-card">
      <div class="settings-card-title">${t('lbl_admin_users')}</div>
      ${users.map(u => `
        <div class="security-row">
          <div>
            <div class="s-name">${esc(u.email)}${u.is_admin ? ` <span class="badge-role owner">${t('lbl_admin_badge')}</span>` : ''}${u.disabled ? ` <span class="badge-role viewer">${t('lbl_disabled_badge')}</span>` : ''}</div>
            <div class="s-sub">${esc(u.name)} · ${t('member_since')} ${esc((u.created_at || '').slice(0, 10))}${u.invited_by ? ` · ${t('lbl_invited_by')} ${esc(u.invited_by)}` : ''}</div>
          </div>
          ${u.id === settingsMe.id ? '' : `<button class="btn-small secondary" onclick="adminSetUserDisabled(${u.id}, ${!u.disabled})">${u.disabled ? t('btn_enable') : t('btn_disable')}</button>`}
        </div>
      `).join('') || `<div class="empty">${t('lbl_none')}</div>`}
    </div>
    <div class="settings-card">
      <div class="settings-card-title">${t('lbl_admin_babies')}</div>
      ${babies.map(b => `
        <div class="security-row">
          <div>
            <div class="s-name">${esc(b.name)}</div>
            <div class="s-sub">${esc(b.birthday || '')} · ${t('lbl_owners')}: ${esc(b.owners.join(', ') || '—')}</div>
          </div>
        </div>
      `).join('') || `<div class="empty">${t('lbl_none')}</div>`}
    </div>
  `;
}

async function adminSetUserDisabled(userId, disable) {
  const res = await fetch(`/api/admin/users/${userId}/${disable ? 'disable' : 'enable'}`, { method: 'POST' });
  if (!res.ok) { await toastError(res); return; }
  toast(t('toast_saved'));
  loadAdminTab();
}

async function adminCreateInvite() {
  const email = document.getElementById('new-invite-email').value.trim();
  const res = await fetch('/api/admin/invites', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) { toast(data.error || t('toast_error')); return; }
  document.getElementById('new-invite-result').innerHTML = `
    <div class="field" style="margin-top:10px;">
      <label>${t('lbl_invite_link_ready')}</label>
      <input type="text" readonly value="${esc(data.link)}" onclick="this.select()">
    </div>
  `;
  document.getElementById('new-invite-email').value = '';
}

async function adminRevokeInvite(id) {
  const res = await fetch(`/api/admin/invites/${id}`, { method: 'DELETE' });
  if (!res.ok) { await toastError(res); return; }
  toast(t('toast_deleted'));
  loadAdminTab();
}

function renderBabyTab() {
  const el = document.getElementById('settings-tab-content');
  let html = babies.map(b => {
    const canEdit = b.role === 'owner' || b.role === 'editor';
    const isOwner = b.role === 'owner';
    const isCurrent = b.id === currentBabyId;
    return `
    <div class="settings-card${isCurrent ? ' current' : ''}" data-id="${b.id}">
      ${isCurrent ? `<div class="pill-current">${t('lbl_current_baby')}</div>` : ''}
      <div style="display:flex;gap:12px;margin-bottom:14px;${isCurrent ? 'margin-top:4px;' : ''}">
        <div class="avatar-circle">${icon('person')}</div>
        <div style="flex:1;display:flex;flex-direction:column;gap:8px;">
          <div class="field" style="margin-bottom:0;"><label>${t('lbl_baby_name')}</label>
            <input type="text" class="baby-name-input" value="${esc(b.name)}" placeholder="${t('baby_name_placeholder')}" ${canEdit ? '' : 'disabled'}>
          </div>
          <div class="field" style="margin-bottom:0;"><label>${t('lbl_birthday')}</label>
            <input type="date" class="baby-birthday-input" value="${esc(b.birthday)}" ${canEdit ? '' : 'disabled'}>
          </div>
        </div>
      </div>
      <div class="field" style="margin-top:6px;padding-top:12px;border-top:1px dashed var(--border);">
        <label>${t('lbl_nap_threshold')}</label>
        <div style="display:flex;align-items:center;gap:10px;">
          <input type="number" class="baby-threshold-input" min="15" max="1440" step="5" style="width:88px;flex:none;" value="${b.nap_threshold_min}" ${canEdit ? '' : 'disabled'}>
          <span style="font-family:ui-monospace,'Cascadia Code','Source Code Pro',monospace;font-size:0.78rem;color:var(--ink2);">${t('lbl_minutes')}</span>
        </div>
        <div class="field-hint" style="margin:6px 0 0;">${t('nap_threshold_hint')}</div>
      </div>
      <div class="field" style="margin-top:6px;">
        <label>${t('lbl_bottle_default')}</label>
        <select class="baby-bottle-default" ${canEdit ? '' : 'disabled'}>
          ${['', 'abgepumpt', 'formula'].map(v => {
            const lbl = v === '' ? t('opt_bottle_ask') : t(v === 'abgepumpt' ? 'opt_pumped' : 'opt_formula');
            const sel = v === (b.bottle_default_content || '') ? ' selected' : '';
            return `<option value="${v}"${sel}>${lbl}</option>`;
          }).join('')}
        </select>
        <div class="field-hint" style="margin:6px 0 0;">${t('bottle_default_hint')}</div>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;">
        <span class="badge-role ${b.role}">${t('role_' + b.role)}</span>
        <div class="baby-actions" style="margin-bottom:0;">
          ${isOwner ? `<button class="btn-small secondary" onclick="toggleBabyAccess(${b.id})">${t('btn_manage_access')}</button>` : ''}
          ${isOwner ? `<button class="btn-small secondary" onclick="deleteBabyRow(${b.id})">${t('btn_delete')}</button>` : ''}
          ${canEdit ? `<button class="btn-small" onclick="saveBabyRow(${b.id})">${t('btn_save')}</button>` : ''}
        </div>
      </div>
      <div class="access-wrap" id="access-wrap-${b.id}" style="display:none;"></div>
    </div>
  `;
  }).join('');
  html += `
    <div class="settings-card add-card">
      <div class="field"><label>${t('lbl_baby_name')}</label>
        <input type="text" id="new-baby-name-input" placeholder="${t('baby_name_placeholder')}">
      </div>
      <div class="field" style="margin-bottom:0;"><label>${t('lbl_birthday')}</label>
        <input type="date" id="new-baby-birthday-input">
      </div>
      <div class="baby-actions" style="margin-bottom:0;margin-top:12px;">
        <button class="btn-small" onclick="addBabyRow()">${t('btn_add_baby')}</button>
      </div>
    </div>
  `;
  el.innerHTML = html;
}

function renderQuickLogTab() {
  const el = document.getElementById('settings-tab-content');
  const selected = getQuickActions();
  el.innerHTML = `
    <div class="settings-card">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:6px;">
        <div class="settings-card-title">${t('settings_quick_title')}</div>
        <div class="count-pill">${selected.length} / 5 ${t('lbl_selected')}</div>
      </div>
      <div style="font-size:0.8rem;font-style:italic;color:var(--ink2);margin-bottom:18px;line-height:1.4;">${t('quick_hint')}</div>
      <div class="type-grid" style="margin-bottom:0;">
        ${QUICK_TYPE_KEYS.map(key => {
          const tp = getType(key);
          const sel = selected.includes(key);
          return `<div class="type-tile${sel ? ' selected' : ''}" onclick="toggleQuickAction('${key}')">
            ${sel ? `<div class="tile-check"><svg viewBox="0 0 24 24">${ICONS.check}</svg></div>` : ''}
            <div class="t-icon">${icon(tp.icon)}</div><div class="t-label">${tp.label}</div>
          </div>`;
        }).join('')}
      </div>
      <div style="margin-top:18px;padding-top:14px;border-top:1px dashed var(--border);font-size:0.74rem;color:var(--ink2);line-height:1.4;">${t('quick_footnote')}</div>
    </div>
  `;
}

function renderAccountTab() {
  const el = document.getElementById('settings-tab-content');
  const me = settingsMe, passkeys = settingsPasskeys;
  let html = `
    <div class="settings-card">
      <div class="settings-card-title">${t('lbl_profile')}</div>
      <div style="display:flex;gap:12px;align-items:flex-end;margin-bottom:14px;">
        <div class="avatar-upload" onclick="document.getElementById('avatar-file-input').click()">
          ${avatarHtml(me.id, me.has_avatar, me.name)}
          <div class="avatar-edit-badge"><svg viewBox="0 0 24 24"><path d="M4 8a2 2 0 0 1 2-2h1.2l.9-1.5A1.6 1.6 0 0 1 9.5 3.7h5a1.6 1.6 0 0 1 1.4.8L16.8 6H18a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z"/><circle cx="12" cy="13" r="3.4"/></svg></div>
        </div>
        <input type="file" id="avatar-file-input" accept="image/jpeg,image/png,image/webp,image/gif" style="display:none;" onchange="uploadAvatar(event)">
        <div class="field" style="flex:1;margin-bottom:0;"><label>${t('lbl_display_name')}</label>
          <input type="text" id="display-name-input" value="${esc(me.name || '')}" placeholder="${t('lbl_display_name')}">
        </div>
      </div>
      <div class="baby-actions" style="margin-bottom:0;">
        ${me.has_avatar ? `<button class="btn-small secondary" onclick="removeAvatar()">${t('btn_remove_photo')}</button>` : ''}
        <button class="btn-small" onclick="saveDisplayName()">${t('btn_save')}</button>
      </div>
      <div class="security-row" style="border-top:1px dashed var(--border);padding-top:14px;margin-top:2px;">
        <div><div class="s-name">${esc(me.email || '')}</div><div class="s-sub">${t('member_since')} ${esc((me.created_at || '').slice(0, 10))} · ${t('last_login')} ${esc((me.last_login_at || '').slice(0, 16).replace('T', ' ')) || '—'}</div></div>
        <button class="btn-small secondary" onclick="doLogout()">${t('btn_logout')}</button>
      </div>
    </div>

    <div class="settings-card">
      <div class="settings-card-title">${icon('note')}${t('settings_logging_title')}</div>
      <div class="security-row">
        <div><div class="s-name">${t('show_notes_label')}</div><div class="s-sub">${t('show_notes_hint')}</div></div>
        <button class="btn-small${me.show_note_fields ? ' secondary' : ''}" onclick="toggleShowNotes()">${me.show_note_fields ? t('btn_disable') : t('btn_enable')}</button>
      </div>
    </div>

    <div class="settings-card">
      <div class="settings-card-title">${icon('bell')}${t('settings_notify_title')}</div>
      <div class="security-row">
        <div><div class="s-name">${t('notify_rhythm_label')}</div><div class="s-sub">${t('notify_hint')}</div></div>
        ${('PushManager' in window)
          ? `<button class="btn-small${me.notify_rhythm ? ' secondary' : ''}" onclick="toggleRhythmNotify()">${me.notify_rhythm ? t('btn_disable') : t('btn_enable')}</button>`
          : `<span class="s-sub" style="text-align:right;max-width:40%;">${t('notify_unsupported')}</span>`}
      </div>
    </div>

    <div class="settings-card">
      <div class="settings-card-title">${icon('shield')}${t('settings_totp_title')}</div>
      <div class="security-row">
        <div><div class="s-name">${me.totp_enabled ? t('totp_enabled_sub') : t('totp_disabled_sub')}</div></div>
        ${me.totp_enabled
          ? `<button class="btn-small secondary" onclick="disableTotp()">${t('btn_disable')}</button>`
          : `<button class="btn-small" onclick="startTotpSetup()">${t('btn_enable')}</button>`}
      </div>
      <div id="totp-setup-wrap"></div>
    </div>

    <div class="settings-card">
      <div class="settings-card-title">${icon('key')}${t('settings_passkeys_title')}</div>
  `;
  html += !passkeys.length
    ? `<div class="empty" style="padding:16px 0;">${t('no_passkeys')}</div>`
    : passkeys.map(p => `
      <div class="security-row">
        <div><div class="s-name">${esc(p.name)}</div><div class="s-sub">${esc((p.created_at || '').slice(0, 10))}</div></div>
        <button class="btn-small secondary" onclick="deletePasskey(${p.id})">${t('btn_delete')}</button>
      </div>
    `).join('');
  html += `
      <div style="margin-top:12px;">
        <button class="ghost-add" id="add-passkey-btn" onclick="addPasskey()" style="display:none;">
          <svg viewBox="0 0 24 24" class="ic" style="width:14px;height:14px;"><path d="M12 5v14M5 12h14"/></svg>
          ${t('btn_add_passkey')}
        </button>
      </div>
    </div>

    <div class="settings-card">
      <div class="settings-card-title">${icon('code')}${t('settings_tokens_title')}</div>
      <div style="font-size:0.78rem;color:var(--ink2);margin-bottom:14px;line-height:1.4;">${t('tokens_hint')}</div>
  `;
  html += !settingsTokens.length
    ? `<div class="empty" style="padding:16px 0;">${t('no_tokens')}</div>`
    : settingsTokens.map(tok => `
      <div class="security-row">
        <div><div class="s-name">${esc(tok.name)}</div><div class="s-sub">${esc(tok.prefix)}… · ${t('last_used')} ${tok.last_used_at ? esc(tok.last_used_at.slice(0, 16).replace('T', ' ')) : t('never_used')}</div></div>
        <button class="btn-small secondary" onclick="deleteToken(${tok.id})">${t('btn_delete')}</button>
      </div>
    `).join('');
  html += `
      <div style="margin-top:12px;">
        <button class="ghost-add" onclick="createToken()">
          <svg viewBox="0 0 24 24" class="ic" style="width:14px;height:14px;"><path d="M12 5v14M5 12h14"/></svg>
          ${t('btn_add_token')}
        </button>
      </div>
    </div>
    <div id="new-token-wrap"></div>

    <div class="settings-card">
      <div class="settings-card-title">${t('settings_danger_title')}</div>
      <div class="security-row">
        <div><div class="s-name">${t('btn_delete_account')}</div><div class="s-sub">${t('delete_account_hint')}</div></div>
        <button class="btn-small secondary" onclick="startDeleteAccount()">${t('btn_delete')}</button>
      </div>
      <div id="delete-account-wrap"></div>
    </div>
  `;
  el.innerHTML = html;
  if (window.PublicKeyCredential) document.getElementById('add-passkey-btn').style.display = '';
}

// ── Security: display name, logout, TOTP, passkeys ──
function urlB64ToU8(b64) {
  const pad = '='.repeat((4 - (b64.length % 4)) % 4);
  const raw = atob((b64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
}

async function toggleRhythmNotify() {
  const on = !settingsMe.notify_rhythm;
  try {
    if (on) {
      const cfg = await (await fetch('/api/push/config')).json();
      if (!cfg.enabled) { toast(t('notify_unavailable')); return; }
      if ((await Notification.requestPermission()) !== 'granted') { toast(t('notify_denied')); return; }
      const reg = await navigator.serviceWorker.ready;
      let sub = await reg.pushManager.getSubscription();
      if (!sub) {
        sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlB64ToU8(cfg.vapid_key),
        });
      }
      const j = sub.toJSON();
      await fetch('/api/push/subscribe', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint: j.endpoint, keys: j.keys, lang }),
      });
    } else {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        await fetch('/api/push/unsubscribe', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ endpoint: sub.endpoint }),
        });
      }
    }
    await fetch('/api/auth/notify', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notify_rhythm: on }),
    });
    settingsMe.notify_rhythm = on;
    renderAccountTab();
    toast(t('toast_saved'));
  } catch (e) {
    toast(t('toast_error'));
  }
}

async function toggleShowNotes() {
  const on = !settingsMe.show_note_fields;
  await fetch('/api/auth/show-notes', {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ show_note_fields: on }),
  });
  settingsMe.show_note_fields = on;
  showNoteFields = on;
  renderAccountTab();
  toast(t('toast_saved'));
}

async function saveDisplayName() {
  const name = document.getElementById('display-name-input').value.trim();
  if (!name) { toast(t('toast_no_name')); return; }
  const res = await fetch('/api/auth/me', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (res.ok) {
    toast(t('toast_saved'));
    loadLog();
  } else {
    toast(t('toast_error'));
  }
}

function uploadAvatar(event) {
  const file = event.target.files[0];
  event.target.value = '';
  if (!file) return;
  if (!file.type.startsWith('image/')) { toast(t('toast_not_an_image')); return; }
  openAvatarCrop(file);
}

// ── Avatar crop ──
// Lets a household member pick which part of a wider photo becomes their
// circular avatar, instead of the server's fixed center-crop guessing for
// them. Server-side re-validates and re-encodes regardless (see
// upload_avatar in main.py) — this only decides the framing.
const CROP_VIEWPORT = 260;
const CROP_OUTPUT = 512;
let cropState = null;

function openAvatarCrop(file) {
  const url = URL.createObjectURL(file);
  const img = new Image();
  img.onload = () => {
    const baseScale = Math.max(CROP_VIEWPORT / img.naturalWidth, CROP_VIEWPORT / img.naturalHeight);
    cropState = {
      img, url,
      naturalW: img.naturalWidth, naturalH: img.naturalHeight,
      baseScale, scale: baseScale, offsetX: 0, offsetY: 0,
      dragging: false, startX: 0, startY: 0, startOffsetX: 0, startOffsetY: 0,
    };
    renderCropModal();
  };
  img.src = url;
}

function renderCropModal() {
  document.getElementById('avatar-crop-title').textContent = t('lbl_crop_photo');
  document.getElementById('avatar-crop-body').innerHTML = `
    <div class="crop-viewport" id="crop-viewport">
      <div class="crop-ring"></div>
    </div>
    <input type="range" class="crop-zoom" id="crop-zoom" min="1" max="3" step="0.01" value="1">
    <div class="crop-hint">${t('crop_hint')}</div>
    <div class="baby-actions" style="margin-top:16px;">
      <button class="btn-small secondary" onclick="closeAvatarCrop()">${t('btn_cancel')}</button>
      <button class="btn-small" onclick="confirmAvatarCrop()">${t('btn_use_photo')}</button>
    </div>
  `;
  const viewport = document.getElementById('crop-viewport');
  viewport.appendChild(cropState.img);
  cropState.img.style.width = cropState.naturalW + 'px';
  cropState.img.style.height = cropState.naturalH + 'px';
  applyCropTransform();

  viewport.addEventListener('pointerdown', cropPointerDown);
  window.addEventListener('pointermove', cropPointerMove);
  window.addEventListener('pointerup', cropPointerUp);
  document.getElementById('crop-zoom').addEventListener('input', cropZoomInput);

  document.getElementById('avatar-crop-overlay').classList.add('open');
}

function clampCropOffset() {
  const s = cropState;
  const drawW = s.naturalW * s.scale;
  const drawH = s.naturalH * s.scale;
  const maxX = (drawW - CROP_VIEWPORT) / 2;
  const maxY = (drawH - CROP_VIEWPORT) / 2;
  s.offsetX = Math.max(-maxX, Math.min(maxX, s.offsetX));
  s.offsetY = Math.max(-maxY, Math.min(maxY, s.offsetY));
}

function applyCropTransform() {
  const s = cropState;
  const drawW = s.naturalW * s.scale;
  const drawH = s.naturalH * s.scale;
  const x = CROP_VIEWPORT / 2 - drawW / 2 + s.offsetX;
  const y = CROP_VIEWPORT / 2 - drawH / 2 + s.offsetY;
  s.img.style.transform = `translate(${x}px, ${y}px) scale(${s.scale})`;
  s.img.style.width = s.naturalW + 'px';
  s.img.style.height = s.naturalH + 'px';
  s.img.style.transformOrigin = '0 0';
}

function cropPointerDown(e) {
  if (!cropState) return;
  cropState.dragging = true;
  cropState.startX = e.clientX;
  cropState.startY = e.clientY;
  cropState.startOffsetX = cropState.offsetX;
  cropState.startOffsetY = cropState.offsetY;
  document.getElementById('crop-viewport').classList.add('dragging');
}
function cropPointerMove(e) {
  if (!cropState || !cropState.dragging) return;
  cropState.offsetX = cropState.startOffsetX + (e.clientX - cropState.startX);
  cropState.offsetY = cropState.startOffsetY + (e.clientY - cropState.startY);
  clampCropOffset();
  applyCropTransform();
}
function cropPointerUp() {
  if (!cropState) return;
  cropState.dragging = false;
  const vp = document.getElementById('crop-viewport');
  if (vp) vp.classList.remove('dragging');
}
function cropZoomInput(e) {
  if (!cropState) return;
  cropState.scale = cropState.baseScale * parseFloat(e.target.value);
  clampCropOffset();
  applyCropTransform();
}

function avatarCropOverlayClick(e) {
  if (e.target === document.getElementById('avatar-crop-overlay')) closeAvatarCrop();
}

function closeAvatarCrop() {
  document.getElementById('avatar-crop-overlay').classList.remove('open');
  window.removeEventListener('pointermove', cropPointerMove);
  window.removeEventListener('pointerup', cropPointerUp);
  if (cropState) {
    URL.revokeObjectURL(cropState.url);
    cropState = null;
  }
}

async function confirmAvatarCrop() {
  const s = cropState;
  if (!s) return;
  const canvas = document.createElement('canvas');
  canvas.width = CROP_OUTPUT;
  canvas.height = CROP_OUTPUT;
  const ctx = canvas.getContext('2d');
  const k = CROP_OUTPUT / CROP_VIEWPORT;
  const drawW = s.naturalW * s.scale;
  const drawH = s.naturalH * s.scale;
  const x = CROP_VIEWPORT / 2 - drawW / 2 + s.offsetX;
  const y = CROP_VIEWPORT / 2 - drawH / 2 + s.offsetY;
  ctx.drawImage(s.img, x * k, y * k, drawW * k, drawH * k);
  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
  closeAvatarCrop();
  const body = new FormData();
  body.append('file', blob, 'avatar.png');
  const res = await fetch('/api/auth/me/avatar', { method: 'POST', body });
  if (!res.ok) { await toastError(res); return; }
  avatarCacheBust = Date.now();
  toast(t('toast_saved'));
  loadSettings();
}

async function removeAvatar() {
  const res = await fetch('/api/auth/me/avatar', { method: 'DELETE' });
  if (!res.ok) { await toastError(res); return; }
  avatarCacheBust = Date.now();
  toast(t('toast_deleted'));
  loadSettings();
}

async function doLogout() {
  // Send what is still waiting while the session is still valid; whatever
  // cannot go now is dropped rather than left to sync under whoever logs
  // in next.
  await syncPending();
  await fetch('/api/auth/logout', { method: 'POST' });
  // Drop the cached journal with the session — on a shared phone the next
  // person must not be able to read it back offline.
  localStorage.removeItem(PENDING_KEY);
  navigator.serviceWorker?.controller?.postMessage('clear-cache');
  location.href = '/login';
}

async function startTotpSetup() {
  const res = await fetch('/api/auth/totp/setup', { method: 'POST' });
  const data = await res.json();
  document.getElementById('totp-setup-wrap').innerHTML = `
    <div class="totp-qr">${data.qr_svg}</div>
    <div class="totp-secret">${esc(data.secret)}</div>
    <div class="field"><input type="text" id="totp-confirm-code" inputmode="numeric" maxlength="6" placeholder="${t('totp_code_placeholder')}"></div>
    <button class="btn" onclick="confirmTotpSetup()">${t('btn_confirm')}</button>
  `;
}

async function confirmTotpSetup() {
  const code = document.getElementById('totp-confirm-code').value.trim();
  const res = await fetch('/api/auth/totp/confirm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });
  if (res.ok) {
    toast(t('toast_saved'));
    loadSettings();
  } else {
    toast(t('toast_error'));
  }
}

async function disableTotp() {
  const password = prompt(t('prompt_password_to_disable'));
  if (!password) return;
  const res = await fetch('/api/auth/totp/disable', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
  if (res.ok) {
    toast(t('toast_saved'));
    loadSettings();
  } else {
    toast(t('toast_error'));
  }
}

// base64url <-> ArrayBuffer, for talking to navigator.credentials
function b64urlToBuf(s) {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  const bin = atob(s);
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
}
function bufToB64url(buf) {
  const bytes = new Uint8Array(buf);
  let bin = '';
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function credentialToJSON(cred) {
  if (typeof cred.toJSON === 'function') return cred.toJSON();
  return {
    id: cred.id,
    rawId: bufToB64url(cred.rawId),
    type: cred.type,
    clientExtensionResults: cred.getClientExtensionResults ? cred.getClientExtensionResults() : {},
    response: {
      clientDataJSON: bufToB64url(cred.response.clientDataJSON),
      attestationObject: bufToB64url(cred.response.attestationObject),
    },
  };
}

async function addPasskey() {
  const name = prompt(t('prompt_passkey_name')) || 'Passkey';
  try {
    const optRes = await fetch('/api/auth/passkey/register/options', { method: 'POST' });
    const opt = await optRes.json();
    const publicKey = {
      ...opt.options,
      challenge: b64urlToBuf(opt.options.challenge),
      user: { ...opt.options.user, id: b64urlToBuf(opt.options.user.id) },
      excludeCredentials: (opt.options.excludeCredentials || []).map(c => ({ ...c, id: b64urlToBuf(c.id) })),
    };
    const cred = await navigator.credentials.create({ publicKey });
    const res = await fetch('/api/auth/passkey/register/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        challenge_token: opt.challenge_token,
        credential: credentialToJSON(cred),
        name,
      }),
    });
    if (res.ok) {
      toast(t('toast_saved'));
      loadSettings();
    } else {
      toast(t('toast_error'));
    }
  } catch (err) {
    toast(err.message || t('toast_error'));
  }
}

async function deletePasskey(id) {
  if (!confirm(t('confirm_delete'))) return;
  await fetch(`/api/auth/passkeys/${id}`, { method: 'DELETE' });
  toast(t('toast_deleted'));
  loadSettings();
}

function createToken() {
  document.getElementById('new-token-wrap').innerHTML = `
    <div class="settings-card">
      <div class="field" style="margin-bottom:0;"><label>${t('prompt_token_name')}</label>
        <input type="text" id="new-token-name-input" placeholder="${t('token_name_placeholder')}">
      </div>
      <div class="baby-actions" style="margin-bottom:0;margin-top:12px;">
        <button class="btn-small" onclick="submitCreateToken()">${t('btn_add_token')}</button>
      </div>
    </div>
  `;
  document.getElementById('new-token-name-input').focus();
}

async function submitCreateToken() {
  const name = document.getElementById('new-token-name-input').value.trim();
  if (!name) { toast(t('toast_no_name')); return; }
  const res = await fetch('/api/auth/tokens', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) { toast(t('toast_error')); return; }
  const data = await res.json();
  settingsTokens = await (await fetch('/api/auth/tokens')).json();
  renderAccountTab();
  document.getElementById('new-token-wrap').innerHTML = `
    <div class="settings-card">
      <div class="settings-card-title">${t('lbl_new_token')}</div>
      <div style="font-size:0.78rem;color:var(--ink2);margin-bottom:10px;line-height:1.4;">${t('token_shown_once')}</div>
      <div class="field" style="margin-bottom:0;">
        <input type="text" readonly value="${esc(data.token)}" onclick="this.select()" style="font-family:ui-monospace,'Cascadia Code','Source Code Pro',monospace;font-size:0.8rem;">
      </div>
    </div>
  `;
}

async function deleteToken(id) {
  if (!confirm(t('confirm_delete_token'))) return;
  await fetch(`/api/auth/tokens/${id}`, { method: 'DELETE' });
  toast(t('toast_deleted'));
  loadSettings();
}

function startDeleteAccount() {
  document.getElementById('delete-account-wrap').innerHTML = `
    <div class="field" style="margin-top:14px;margin-bottom:0;"><label>${t('prompt_password_to_delete_account')}</label>
      <input type="password" id="delete-account-password-input" autocomplete="current-password">
    </div>
    <div class="baby-actions" style="margin-bottom:0;margin-top:12px;">
      <button class="btn-small secondary" onclick="submitDeleteAccount()">${t('btn_confirm')}</button>
    </div>
  `;
  document.getElementById('delete-account-password-input').focus();
}

async function submitDeleteAccount() {
  const password = document.getElementById('delete-account-password-input').value;
  if (!password) return;
  if (!confirm(t('confirm_delete_account'))) return;
  const res = await fetch('/api/auth/me', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
  if (!res.ok) { await toastError(res); return; }
  location.href = '/login';
}

async function toggleQuickAction(key) {
  let actions = getQuickActions();
  if (actions.includes(key)) {
    actions = actions.filter(k => k !== key);
  } else {
    if (actions.length >= 5) { toast(t('quick_max_toast')); return; }
    actions.push(key);
  }
  await setQuickActions(actions);
  loadSettings();
}

async function saveBabyRow(id) {
  const row = document.querySelector(`.settings-card[data-id="${id}"]`);
  const name = row.querySelector('.baby-name-input').value;
  const birthday = row.querySelector('.baby-birthday-input').value;
  const nap_threshold_min = parseInt(row.querySelector('.baby-threshold-input').value, 10);
  const bottle_default_content = row.querySelector('.baby-bottle-default').value;
  const res = await fetch(`/api/babies/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, birthday, nap_threshold_min, bottle_default_content }),
  });
  if (!res.ok) { await toastError(res); return; }
  await loadBabies();
  toast(t('toast_saved'));
  renderBirthdayBanner();
}

async function deleteBabyRow(id) {
  if (!confirm(t('confirm_delete_baby'))) return;
  await fetch(`/api/babies/${id}`, { method: 'DELETE' });
  await loadBabies();
  toast(t('toast_deleted'));
  renderBirthdayBanner();
  loadLog();
  loadSettings();
}

async function addBabyRow() {
  const name = document.getElementById('new-baby-name-input').value.trim();
  const birthday = document.getElementById('new-baby-birthday-input').value;
  if (!name) { toast(t('toast_no_name')); return; }
  const res = await fetch('/api/babies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, birthday }),
  });
  if (res.ok) {
    const created = await res.json();
    await loadBabies();
    switchBaby(created.id);
    toast(t('toast_saved'));
    loadSettings();
  } else {
    toast(t('toast_error'));
  }
}

async function toggleBabyAccess(babyId) {
  const wrap = document.getElementById(`access-wrap-${babyId}`);
  const open = wrap.style.display !== 'none';
  wrap.style.display = open ? 'none' : '';
  if (!open) await loadBabyAccess(babyId);
}

async function loadBabyAccess(babyId) {
  const wrap = document.getElementById(`access-wrap-${babyId}`);
  const res = await fetch(`/api/babies/${babyId}/access`);
  const members = res.ok ? await res.json() : [];
  const baby = babies.find(b => b.id === babyId);
  wrap.innerHTML = `
    <div class="label" style="margin:16px 0 10px;padding-top:14px;border-top:1px solid var(--border);">${t('lbl_shared_with')}</div>
    ${members.map(m => {
      const isCreator = baby && baby.created_by === m.user_id;
      return `
      <div class="security-row">
        <div style="display:flex;align-items:center;gap:9px;">
          ${avatarHtml(m.user_id, m.has_avatar, m.email, 'sm')}
          <div><div class="s-name">${esc(m.email)}</div>${isCreator ? `<div class="s-sub">${t('lbl_baby_creator')}</div>` : ''}</div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          ${isCreator
            ? `<span class="badge-role ${m.role}">${t('role_' + m.role)}</span>`
            : `<select class="role-select" data-baby-id="${babyId}" data-email="${esc(m.email)}" onchange="changeBabyAccessRole(this)">
                 <option value="viewer" ${m.role === 'viewer' ? 'selected' : ''}>${t('role_viewer')}</option>
                 <option value="editor" ${m.role === 'editor' ? 'selected' : ''}>${t('role_editor')}</option>
                 <option value="owner" ${m.role === 'owner' ? 'selected' : ''}>${t('role_owner')}</option>
               </select>
               <svg viewBox="0 0 24 24" class="ic" style="width:16px;height:16px;color:var(--ink2);cursor:pointer;" onclick="revokeBabyAccess(${babyId},${m.user_id})"><path d="M6 6l12 12M18 6L6 18"/></svg>`
          }
        </div>
      </div>
    `;
    }).join('')}
    <div class="field"><label>${t('lbl_invite_email')}</label>
      <input type="email" id="invite-email-${babyId}" placeholder="name@example.com">
    </div>
    <div class="field"><label>${t('lbl_role')}</label>
      <select id="invite-role-${babyId}">
        <option value="viewer">${t('role_viewer')}</option>
        <option value="editor" selected>${t('role_editor')}</option>
        <option value="owner">${t('role_owner')}</option>
      </select>
    </div>
    <div class="baby-actions">
      <button class="btn-small" onclick="grantBabyAccess(${babyId})">${t('btn_invite')}</button>
    </div>
  `;
}

async function grantBabyAccess(babyId) {
  const email = document.getElementById(`invite-email-${babyId}`).value.trim();
  const role = document.getElementById(`invite-role-${babyId}`).value;
  if (!email) { toast(t('toast_no_name')); return; }
  const res = await fetch(`/api/babies/${babyId}/access`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, role }),
  });
  const data = await res.json();
  if (res.ok) {
    toast(t('toast_saved'));
    loadBabyAccess(babyId);
  } else {
    toast(data.error || t('toast_error'));
  }
}

async function changeBabyAccessRole(selectEl) {
  const babyId = selectEl.dataset.babyId;
  const email = selectEl.dataset.email;
  const role = selectEl.value;
  const res = await fetch(`/api/babies/${babyId}/access`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, role }),
  });
  const data = await res.json().catch(() => ({}));
  if (res.ok) {
    toast(t('toast_saved'));
  } else {
    toast(data.error || t('toast_error'));
    loadBabyAccess(parseInt(babyId, 10));
  }
}

async function revokeBabyAccess(babyId, userId) {
  if (!confirm(t('confirm_remove_access'))) return;
  const res = await fetch(`/api/babies/${babyId}/access/${userId}`, { method: 'DELETE' });
  const data = await res.json().catch(() => ({}));
  if (res.ok) {
    toast(t('toast_deleted'));
    loadBabyAccess(babyId);
  } else {
    toast(data.error || t('toast_error'));
  }
}

// ── Modal ──
function openModal() {
  editEntryId = null;
  selectedType = null;
  document.querySelectorAll('.type-tile').forEach(tp => tp.classList.remove('selected'));
  document.getElementById('form-fields').innerHTML = '';
  document.getElementById('form-fields').classList.remove('visible');
  document.getElementById('modal-title').textContent = t('modal_new');

  const grid = document.getElementById('type-grid');
  grid.style.display = '';
  document.getElementById('tile-sleep_start').style.display = openSleepEntry ? 'none' : '';
  document.getElementById('tile-walk').style.display = openWalkEntry ? 'none' : '';

  document.getElementById('modal-overlay').classList.add('open');
}
function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
}
function overlayClick(e) {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
}

/** Weight/height is measured rarely, so it's reached from Stats instead of the FAB's everyday type grid. */
function openMeasurementModal() {
  editEntryId = null;
  selectedType = null;
  document.getElementById('form-fields').innerHTML = '';
  document.getElementById('form-fields').classList.remove('visible');
  document.getElementById('type-grid').style.display = 'none';
  document.getElementById('modal-overlay').classList.add('open');
  selectType('weight');
}

function selectType(type) {
  selectedType = type;
  document.querySelectorAll('.type-tile').forEach(tp => tp.classList.remove('selected'));
  const found = [...document.querySelectorAll('.type-tile')].find(tp =>
    tp.onclick?.toString().includes(`'${type}'`) || tp.dataset.type === type
  );
  if (found) found.classList.add('selected');

  const now = nowLocal();
  const fields = document.getElementById('form-fields');
  fields.classList.add('visible');

  if (type === 'sleep_start') {
    document.getElementById('modal-title').textContent = t('tile_sleep_start');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      ${noteFieldHtml()}
      <button class="btn" onclick="submitEntry()">${t('btn_save_sleep')}</button>
    `;
  } else if (type === 'diaper') {
    document.getElementById('modal-title').textContent = t('tile_diaper');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_type')}</label>
        <select id="f-diaper-type">
          <option value="nass">${t('opt_wet')}</option>
          <option value="schmutzig">${t('opt_dirty')}</option>
          <option value="beides">${t('opt_both')}</option>
        </select>
      </div>
      ${noteFieldHtml()}
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'nursing') {
    document.getElementById('modal-title').textContent = t('tile_nursing');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_start'), now)}
      ${dtField('f-end', t('lbl_end'), '')}
      <div class="field"><label>${t('lbl_side')}</label>
        <select id="f-side">
          <option value="">—</option>
          <option value="links">${t('opt_left')}</option>
          <option value="rechts">${t('opt_right')}</option>
          <option value="beide">${t('opt_both_sides')}</option>
        </select>
      </div>
      ${noteFieldHtml()}
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'bottle') {
    document.getElementById('modal-title').textContent = t('tile_bottle');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_amount')}</label><input type="number" id="f-amount" min="0" step="5" placeholder="120"></div>
      <div class="field"><label>${t('lbl_content')}</label>
        <select id="f-content">${bottleContentOptions()}</select>
      </div>
      ${noteFieldHtml()}
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'weight') {
    document.getElementById('modal-title').textContent = t('tile_weight');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_weight_g')}</label><input type="number" id="f-weight" min="0" step="10" placeholder="3450"></div>
      <div class="field"><label>${t('lbl_height_cm')}</label><input type="number" id="f-height" min="0" step="0.5" placeholder="52"></div>
      ${noteFieldHtml()}
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'walk') {
    document.getElementById('modal-title').textContent = t('tile_walk');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      ${noteFieldHtml()}
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'clothing') {
    document.getElementById('modal-title').textContent = t('tile_clothing');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      ${noteFieldHtml()}
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'mood') {
    document.getElementById('modal-title').textContent = t('tile_mood');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_mood')}</label>
        <select id="f-mood">
          <option value="happy">${t('opt_mood_happy')}</option>
          <option value="neutral">${t('opt_mood_neutral')}</option>
          <option value="fussy">${t('opt_mood_fussy')}</option>
          <option value="crying">${t('opt_mood_crying')}</option>
        </select>
      </div>
      ${noteFieldHtml()}
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else {
    document.getElementById('modal-title').textContent = t('tile_note');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="3"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  }
}

async function submitEntry() {
  const start = readDT('f-start');
  if (!start) { toast(t('toast_no_time')); return; }
  const meta = {};
  if (selectedType === 'diaper') meta.diaper_type = document.getElementById('f-diaper-type')?.value;
  if (selectedType === 'nursing') meta.side = document.getElementById('f-side')?.value;
  if (selectedType === 'bottle') {
    meta.amount = document.getElementById('f-amount')?.value;
    meta.content = document.getElementById('f-content')?.value;
  }
  if (selectedType === 'weight') {
    meta.weight = document.getElementById('f-weight')?.value;
    meta.height = document.getElementById('f-height')?.value;
    if (!meta.weight && !meta.height) { toast(t('toast_no_measurement')); return; }
  }
  if (selectedType === 'mood') meta.mood = document.getElementById('f-mood')?.value;

  const apiType = selectedType === 'sleep_start' ? 'sleep' : selectedType;

  const endLocal = readDT('f-end');
  const body = {
    type: apiType,
    ts_start: toUtc(start),
    ts_end: endLocal ? toUtc(endLocal) : null,
    note: document.getElementById('f-note')?.value || '',
    meta,
  };

  const r = await createEntry(body);
  if (r.failed) { await toastError(r.failed); return; }

  const saved = r.saved || { ...body, localId: r.queued.localId, pending: true };
  if (apiType === 'sleep' && !saved.ts_end) openSleepEntry = saved;
  if (apiType === 'walk' && !saved.ts_end) openWalkEntry = saved;
  closeModal();
  if (r.saved) toast(t('toast_saved'));
  showDayOf(toUtc(start));
  loadLog();
}

// ── Edit existing entry ──
function openEditModal(id) {
  const entry = currentEntries.find(e => e.id === id);
  if (!entry) return;
  editEntryId = id;
  selectedType = null;
  document.querySelectorAll('.type-tile').forEach(tp => tp.classList.remove('selected'));
  document.getElementById('type-grid').style.display = 'none';
  const tp = getType(entry.type);
  document.getElementById('modal-title').textContent = tp.label;
  const fields = document.getElementById('form-fields');
  fields.classList.add('visible');
  fields.innerHTML = editFieldsHtml(entry);
  document.getElementById('modal-overlay').classList.add('open');
}

function editFieldsHtml(entry) {
  const m = entry.meta || {};
  const start = toLocalDT(entry.ts_start);
  const end = toLocalDT(entry.ts_end);
  const note = esc(entry.note || '');

  if (entry.type === 'diaper') {
    return `
      ${dtField('f-start', t('lbl_time'), start)}
      <div class="field"><label>${t('lbl_type')}</label>
        <select id="f-diaper-type">
          <option value="nass" ${m.diaper_type === 'nass' ? 'selected' : ''}>${t('opt_wet')}</option>
          <option value="schmutzig" ${m.diaper_type === 'schmutzig' ? 'selected' : ''}>${t('opt_dirty')}</option>
          <option value="beides" ${m.diaper_type === 'beides' ? 'selected' : ''}>${t('opt_both')}</option>
        </select>
      </div>
      ${noteFieldHtml(note)}
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'nursing') {
    return `
      ${dtField('f-start', t('lbl_start'), start)}
      ${dtField('f-end', t('lbl_end'), end)}
      <div class="field"><label>${t('lbl_side')}</label>
        <select id="f-side">
          <option value="">—</option>
          <option value="links" ${m.side === 'links' ? 'selected' : ''}>${t('opt_left')}</option>
          <option value="rechts" ${m.side === 'rechts' ? 'selected' : ''}>${t('opt_right')}</option>
          <option value="beide" ${m.side === 'beide' ? 'selected' : ''}>${t('opt_both_sides')}</option>
        </select>
      </div>
      ${noteFieldHtml(note)}
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'bottle') {
    return `
      ${dtField('f-start', t('lbl_time'), start)}
      <div class="field"><label>${t('lbl_amount')}</label><input type="number" id="f-amount" min="0" step="5" value="${esc(String(m.amount ?? ''))}"></div>
      <div class="field"><label>${t('lbl_content')}</label>
        <select id="f-content">
          <option value="abgepumpt" ${m.content === 'abgepumpt' ? 'selected' : ''}>${t('opt_pumped')}</option>
          <option value="formula" ${m.content === 'formula' ? 'selected' : ''}>${t('opt_formula')}</option>
        </select>
      </div>
      ${noteFieldHtml(note)}
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'sleep') {
    return `
      ${dtField('f-start', t('lbl_start'), start)}
      ${dtField('f-end', t('lbl_end'), end)}
      ${noteFieldHtml(note)}
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'weight') {
    return `
      ${dtField('f-start', t('lbl_time'), start)}
      <div class="field"><label>${t('lbl_weight_g')}</label><input type="number" id="f-weight" min="0" step="10" value="${esc(String(m.weight ?? ''))}"></div>
      <div class="field"><label>${t('lbl_height_cm')}</label><input type="number" id="f-height" min="0" step="0.5" value="${esc(String(m.height ?? ''))}"></div>
      ${noteFieldHtml(note)}
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'walk') {
    return `
      ${dtField('f-start', t('lbl_start'), start)}
      ${dtField('f-end', t('lbl_end'), end)}
      ${noteFieldHtml(note)}
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'mood') {
    return `
      ${dtField('f-start', t('lbl_time'), start)}
      <div class="field"><label>${t('lbl_mood')}</label>
        <select id="f-mood">
          <option value="happy" ${m.mood === 'happy' ? 'selected' : ''}>${t('opt_mood_happy')}</option>
          <option value="neutral" ${m.mood === 'neutral' ? 'selected' : ''}>${t('opt_mood_neutral')}</option>
          <option value="fussy" ${m.mood === 'fussy' ? 'selected' : ''}>${t('opt_mood_fussy')}</option>
          <option value="crying" ${m.mood === 'crying' ? 'selected' : ''}>${t('opt_mood_crying')}</option>
        </select>
      </div>
      ${noteFieldHtml(note)}
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  // Reached by clothing (toggle applies) and note (the field is the entry,
  // so it always shows).
  const notes = entry.type === 'note'
    ? `<div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="3">${note}</textarea></div>`
    : noteFieldHtml(note, 3);
  return `
    ${dtField('f-start', t('lbl_time'), start)}
    ${notes}
    <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
  `;
}

async function submitEditEntry() {
  const start = readDT('f-start');
  if (!start) { toast(t('toast_no_time')); return; }
  const entry = currentEntries.find(e => e.id === editEntryId);
  if (!entry) return;

  const meta = {};
  if (entry.type === 'diaper') meta.diaper_type = document.getElementById('f-diaper-type')?.value;
  if (entry.type === 'nursing') meta.side = document.getElementById('f-side')?.value;
  if (entry.type === 'bottle') {
    meta.amount = document.getElementById('f-amount')?.value;
    meta.content = document.getElementById('f-content')?.value;
  }
  if (entry.type === 'weight') {
    meta.weight = document.getElementById('f-weight')?.value;
    meta.height = document.getElementById('f-height')?.value;
    if (!meta.weight && !meta.height) { toast(t('toast_no_measurement')); return; }
  }
  if (entry.type === 'mood') meta.mood = document.getElementById('f-mood')?.value;

  const endLocal = readDT('f-end');
  const body = {
    ts_start: toUtc(start),
    ts_end: endLocal ? toUtc(endLocal) : null,
    // The toggle can hide the field on an entry that already has a note
    // (logged before it was turned off, or from another device) — leave
    // that note as it was rather than wiping it because the field wasn't
    // on screen to resave it.
    note: document.getElementById('f-note')?.value ?? entry.note ?? '',
    meta,
  };

  const res = await fetch(`/api/entries/${editEntryId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (res.ok) {
    closeModal();
    toast(t('toast_saved'));
    // Unlike creating an entry, editing shouldn't relocate the viewport —
    // an overnight sleep edited from today's view still belongs on today
    // even though it started yesterday.
    loadLog();
  } else {
    await toastError(res);
  }
}

// ── Toast ──
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2200);
}

// ── Swipe to switch tabs ──
const TAB_ORDER = ['log', 'stats', 'settings'];
function initSwipe() {
  const main = document.querySelector('.main');
  let sx = 0, sy = 0, tracking = false;
  main.addEventListener('touchstart', (e) => {
    if (e.touches.length !== 1) return;
    sx = e.touches[0].clientX;
    sy = e.touches[0].clientY;
    tracking = true;
  }, { passive: true });
  main.addEventListener('touchend', (e) => {
    if (!tracking) return;
    tracking = false;
    const dx = e.changedTouches[0].clientX - sx;
    const dy = e.changedTouches[0].clientY - sy;
    if (Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
    const current = document.querySelector('.tab-page.active').id.replace('tab-', '');
    const idx = TAB_ORDER.indexOf(current) + (dx < 0 ? 1 : -1);
    if (idx < 0 || idx >= TAB_ORDER.length) return;
    const name = TAB_ORDER[idx];
    switchTab(name, document.getElementById('tab-btn-' + name));
  }, { passive: true });
  main.addEventListener('touchcancel', () => { tracking = false; }, { passive: true });
}

// ── Export ──
let exportRange = 'today';
function selectRange(r) {
  exportRange = r;
  document.querySelectorAll('.range-pill').forEach(b => b.classList.toggle('active', b.dataset.range === r));
  document.getElementById('custom-range').classList.toggle('visible', r === 'custom');
}
function exportDates() {
  const today = todayStr();
  if (exportRange === 'today') return { start: today, end: today };
  if (exportRange === 'week') {
    const d = new Date();
    const monday = new Date(d);
    monday.setDate(d.getDate() - ((d.getDay() + 6) % 7));
    return { start: `${monday.getFullYear()}-${pad(monday.getMonth()+1)}-${pad(monday.getDate())}`, end: today };
  }
  if (exportRange === 'month') {
    const d = new Date();
    return { start: `${d.getFullYear()}-${pad(d.getMonth()+1)}-01`, end: today };
  }
  const start = document.getElementById('export-start').value || today;
  const end = document.getElementById('export-end').value || today;
  return { start, end };
}
function openReport() {
  const { start, end } = exportDates();
  window.open(`/report?start=${start}&end=${end}&baby_id=${currentBabyId}`, '_blank');
}
function downloadCsv() {
  const { start, end } = exportDates();
  window.location.href = `/api/export.csv?start=${start}&end=${end}&baby_id=${currentBabyId}`;
}

// ── Offline state ──
// Cached entries look exactly like live ones, so say plainly when what is
// on screen is a saved copy rather than the household's current log.
function setOffline(off) {
  const bar = document.getElementById('offline-bar');
  if (!bar) return;
  bar.textContent = t('offline_bar');
  bar.hidden = !off;
}
// Refetch when the link comes back; the response itself settles the state.
window.addEventListener('online', () => syncPending().then(loadLog));
window.addEventListener('offline', () => setOffline(true));

// ── Midnight rollover ──
// The day is picked once at script start, but this app is left open for
// hours — a phone put down at 23:30 and picked up the next morning is the
// normal case. Without a re-check the view stays on the day it started on:
// the label still reads "Today", the entries are yesterday's, and the
// forward arrow is disabled, so there is no way out but the date picker.
// Polling rather than only listening, because which lifecycle events a
// suspended PWA gets on resume is up to the platform.
const DAY_CHECK_MS = 30000;
function checkDayRollover() {
  const fresh = storedDate();
  if (fresh === currentDate) return;
  currentDate = fresh;
  updateDayNav();
  loadLog();
  if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
}
setInterval(() => { checkDayRollover(); syncPending(); }, DAY_CHECK_MS);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) checkDayRollover();
});
window.addEventListener('pageshow', checkDayRollover);

// ── Live sync (SSE) ──
function initEvents() {
  const es = new EventSource('/api/events');
  es.onmessage = () => {
    loadLog();
    if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
  };
  es.onerror = () => {};
}

// ── Init ──
initUI();
updateDayNav();
setLogView(logView);
initEvents();
initSwipe();
document.getElementById('export-start').value = todayStr();
document.getElementById('export-end').value = todayStr();
(async () => {
  await loadQuickActions();
  await loadBabies();
  renderBirthdayBanner();
  await syncPending();
  loadLog();
  const initialTab = TAB_ORDER.includes(location.hash.slice(1)) ? location.hash.slice(1) : 'log';
  if (initialTab !== 'log') switchTab(initialTab);
})();

let tlResizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(tlResizeTimer);
  tlResizeTimer = setTimeout(() => { if (logView === 'timeline') renderTimeline(); }, 200);
});
setInterval(() => {
  if (logView === 'timeline' && document.getElementById('tab-log').classList.contains('active')) renderTimeline();
}, 60000);

// PWA install eligibility on Android needs an active service worker; it
// also serves the app and the last-loaded log back when there is no network.
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js");
}
