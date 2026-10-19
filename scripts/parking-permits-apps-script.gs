/**
 * PARKING PERMIT AUTOMATION
 * -------------------------------------------------------------
 * A row appears in the "Guests" sheet (added by the AI OS from Lodgify,
 * or by hand). This script:
 *  1. Emails the property manager the guest + vehicle details with a Confirm button
 *  2. Sends reminders every 2 hours (up to 3) if nobody confirms, copying the shared inbox
 *  3. After the 3rd reminder with no confirmation, marks the row "Manual intervention"
 *  4. When a manager confirms: marks the row "Confirmed" and emails the shared inbox.
 *     Guest confirmations are SWITCHED OFF during testing - see sendConfirmationEmails_.
 *
 * Column L (Permit length) is a sheet formula covering the guest's whole stay,
 * check-in day to check-out day inclusive. Column M (Notes) carries AI OS
 * notes, such as a guest having no email on file.
 *
 * Only edit the CONFIG section below.
 */

const CONFIG = {
  // Fill these in before going live
  MANAGER_EMAIL: 'ademolajoyce@yahoo.co.uk',
  SHARED_INBOX: 'bankoledada@gmail.com',
  PROPERTY_NAME: 'Modern Digbeth Stay',
  BUSINESS_NAME: 'Overcomers Property Limited',

  // The address the emails should appear to come from (also used for replies).
  FROM_EMAIL: 'overcomersproperty@gmail.com',

  // TRUE  = send "from" FROM_EMAIL (only works if the account running the script
  //         owns it or has it set up as a "Send mail as" address).
  // FALSE = send from the account that owns the sheet, with your business name
  //         as the sender name, and replies going to FROM_EMAIL.
  SEND_FROM_ALIAS: false,

  // TRUE = every email goes to a test address only (safe for testing).
  // Change to false only when you are happy with the test results.
  TEST_MODE: true,

  // Only used while TEST_MODE is true: the "manager" email goes to this address
  // instead of the real manager. Leave as '' to send it to SHARED_INBOX.
  TEST_MANAGER_EMAIL: 'info@webawesome.co.uk',

  // Paste the "Web app URL" from Deploy > Manage deployments here (it must end in /exec).
  // If left empty, the script tries to find it by itself, which can pick the wrong link.
  WEB_APP_URL: 'https://script.google.com/macros/s/AKfycbxS6DuCiOPY0WKyPimASM5Xfv1RxFDkoRXqmxJWqvvPqh6A4Kj-mtN7Jnv6T8MeScw6/exec',

  SHEET_NAME: 'Guests',

  // Reminders go out every REMINDER_EVERY_HOURS while unconfirmed, up to MAX_REMINDERS.
  // After the last reminder, if still unconfirmed, the row is marked "Manual intervention".
  REMINDER_EVERY_HOURS: 2,
  MAX_REMINDERS: 3,

  TIMEZONE: 'Europe/London'
};

// Column numbers in the sheet (A = 1, B = 2, ...)
const COL = {
  NAME: 1,          // A  Guest name
  GUEST_EMAIL: 2,   // B  Guest email
  REG: 3,           // C  Vehicle registration
  VEHICLE: 4,       // D  Car make/model/colour
  CHECKIN: 5,       // E  Check-in date
  CHECKOUT: 6,      // F  Check-out date
  STATUS: 7,        // G  Status (filled in by the script)
  SENT_AT: 8,       // H  Email sent time
  CONFIRMED_AT: 9,  // I  Confirmed time
  REMINDERS: 10,    // J  Reminders sent (script use)
  TOKEN: 11,        // K  Secret confirm code (script use, hidden)
  LENGTH: 12,       // L  Permit length in days (sheet formula, do not edit)
  NOTES: 13         // M  Notes from the AI OS (e.g. no email on file)
};

const HEADERS = [
  'Guest name', 'Guest email', 'Vehicle registration', 'Car make/model/colour',
  'Check-in date', 'Check-out date', 'Status', 'Email sent time',
  'Confirmed time', 'Reminders sent', 'Confirm code', 'Permit length (days)', 'Notes'
];

// Statuses a manager is allowed to confirm
const CONFIRMABLE_STATUSES = ['Sent', 'Manual intervention'];

/* ============================================================
 * ONE-TIME SETUP  (run this once from the Apps Script editor)
 * ============================================================ */
function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(CONFIG.SHEET_NAME);

  sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold');
  sheet.setFrozenRows(1);
  sheet.getRange(2, COL.CHECKIN, 1000, 2).setNumberFormat('dd/mm/yyyy');
  sheet.getRange(2, COL.SENT_AT, 1000, 2).setNumberFormat('dd/mm/yyyy hh:mm');
  sheet.hideColumns(COL.TOKEN);

  // Permit length in days (column L): the guest is covered from the check-in
  // day to the check-out day inclusive (check-out minus check-in plus one).
  // Blank if the dates are missing, invalid, or the check-in is before 2020.
  const lengthFormulas = [];
  for (let r = 2; r <= 1001; r++) {
    lengthFormulas.push(['=IF(AND(ISNUMBER(E' + r + '),ISNUMBER(F' + r + ')),' +
      'IF(AND(E' + r + '>DATE(2020,1,1),F' + r + '>=E' + r + '),F' + r + '-E' + r + '+1),"")']);
  }
  sheet.getRange(2, COL.LENGTH, 1000, 1).setFormulas(lengthFormulas);

  // Remove old triggers for this script, then check the sheet every 5 minutes
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'processRows') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('processRows').timeBased().everyMinutes(5).create();

  SpreadsheetApp.getUi().alert('Setup complete. Next step: deploy as a web app (see the setup guide).');
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Parking Permits')
    .addItem('Run check now', 'processRows')
    .addToUi();
}

/* ============================================================
 * MAIN JOB  (runs every 5 minutes)
 * ============================================================ */
function processRows() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) return;
  try {
    const sheet = getSheet_();
    const lastRow = sheet.getLastRow();
    if (lastRow < 2) return;

    const rows = sheet.getRange(2, 1, lastRow - 1, HEADERS.length).getValues();
    const now = new Date();
    const today = startOfToday_();

    rows.forEach(function (r, i) {
      const rowNum = i + 2;
      const status = String(r[COL.STATUS - 1]).trim();
      if (status === '') {
        handleNewRow_(sheet, rowNum, r, today);
      } else if (status === 'Sent') {
        handleReminders_(sheet, rowNum, r, now);
      }
    });
  } finally {
    lock.releaseLock();
  }
}

function handleNewRow_(sheet, rowNum, r, today) {
  const name = String(r[COL.NAME - 1]).trim();
  const guestEmail = String(r[COL.GUEST_EMAIL - 1]).trim();
  const reg = String(r[COL.REG - 1]).trim();
  const vehicle = String(r[COL.VEHICLE - 1]).trim();
  const checkin = r[COL.CHECKIN - 1];
  const checkout = r[COL.CHECKOUT - 1];
  const notes = String(r[COL.NOTES - 1]).trim();

  // Row still being typed? Wait until the essentials are filled in.
  // A guest email is NOT required - the permit still gets processed, and the
  // Notes column tells the team to collect an email so the guest can be told.
  if (!name || !reg || !vehicle || !checkin || !checkout) return;

  if (!(checkin instanceof Date) || !(checkout instanceof Date)) {
    setStatus_(sheet, rowNum, 'Check the dates');
    return;
  }
  if (checkout < today) {
    setStatus_(sheet, rowNum, 'Not sent - stay in the past');
    return;
  }

  // Mark as "Sending" first so the same row can never be emailed twice
  const token = Utilities.getUuid();
  sheet.getRange(rowNum, COL.TOKEN).setValue(token);
  setStatus_(sheet, rowNum, 'Sending');
  SpreadsheetApp.flush();

  try {
    sendManagerEmail_({
      name: name, reg: reg, vehicle: vehicle,
      checkin: checkin, checkout: checkout, notes: notes
    }, token, 0);
    sheet.getRange(rowNum, COL.SENT_AT).setValue(new Date());
    sheet.getRange(rowNum, COL.REMINDERS).setValue(0);
    setStatus_(sheet, rowNum, 'Sent');
  } catch (err) {
    setStatus_(sheet, rowNum, 'Error: ' + err.message);
  }
}

function handleReminders_(sheet, rowNum, r, now) {
  const sentAt = r[COL.SENT_AT - 1];
  if (!(sentAt instanceof Date)) return;

  const sent = Number(r[COL.REMINDERS - 1]) || 0;
  const hours = (now - sentAt) / 36e5;
  const token = String(r[COL.TOKEN - 1]);
  const details = {
    name: String(r[COL.NAME - 1]),
    reg: String(r[COL.REG - 1]),
    vehicle: String(r[COL.VEHICLE - 1]),
    checkin: r[COL.CHECKIN - 1],
    checkout: r[COL.CHECKOUT - 1],
    notes: String(r[COL.NOTES - 1])
  };

  if (sent < CONFIG.MAX_REMINDERS) {
    // Reminder n is due at REMINDER_EVERY_HOURS * n after the original email
    if (hours < CONFIG.REMINDER_EVERY_HOURS * (sent + 1)) return;
    try {
      sendManagerEmail_(details, token, sent + 1);
      sheet.getRange(rowNum, COL.REMINDERS).setValue(sent + 1);
    } catch (err) {
      // Leave the row as it is; the next run will try again
    }
  } else if (hours >= CONFIG.REMINDER_EVERY_HOURS * (CONFIG.MAX_REMINDERS + 1)) {
    // All reminders sent and still not confirmed: hand over to a person
    setStatus_(sheet, rowNum, 'Manual intervention');
  }
}

/* ============================================================
 * EMAILS
 * ============================================================ */
function sendManagerEmail_(d, token, level) {
  const url = CONFIG.WEB_APP_URL || ScriptApp.getService().getUrl();
  if (!url) throw new Error('Web app not deployed yet');
  const confirmUrl = url + '?t=' + encodeURIComponent(token);

  let heading = 'New parking permit needed';
  let subject = 'Parking permit needed - ' + d.reg + ' - ' + CONFIG.PROPERTY_NAME;
  let banner = '';
  if (level === 1) {
    heading = 'Reminder: parking permit not yet confirmed';
    subject = 'REMINDER: ' + subject;
    banner = '<p style="color:#b45309"><b>This permit has not been confirmed yet. Please action it as soon as you can.</b></p>';
  } else if (level >= 2) {
    heading = 'URGENT: parking permit still not confirmed';
    subject = 'URGENT: ' + subject;
    banner = '<p style="color:#b91c1c"><b>This is a further reminder. The guest needs their parking covered. Please action it now.</b></p>';
  }

  const html =
    '<div style="font-family:Arial,sans-serif;max-width:560px">' +
    '<h2>' + esc_(heading) + '</h2>' + banner +
    '<p>Please add the following vehicle to the permit list for <b>' + esc_(CONFIG.PROPERTY_NAME) + '</b>:</p>' +
    detailsTable_(d) +
    '<p>When the permit has been added, click the button below.</p>' +
    '<p><a href="' + confirmUrl + '" style="background:#15803d;color:#ffffff;padding:12px 24px;' +
    'text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block">Confirm permit added</a></p>' +
    '<p style="color:#666;font-size:12px">Sent by ' + esc_(CONFIG.BUSINESS_NAME) + '</p>' +
    '</div>';

  const opts = { name: CONFIG.BUSINESS_NAME, htmlBody: html };
  if (CONFIG.TEST_MODE) {
    subject = '[TEST] ' + subject;
    sendMail_(CONFIG.TEST_MANAGER_EMAIL || CONFIG.SHARED_INBOX, subject, '', opts);
  } else {
    if (level > 0) opts.cc = CONFIG.SHARED_INBOX;
    sendMail_(CONFIG.MANAGER_EMAIL, subject, '', opts);
  }
}

function sendConfirmationEmails_(d, guestEmail, confirmedAt) {
  const prefix = CONFIG.TEST_MODE ? '[TEST] ' : '';

  // TESTING: guest confirmations are SWITCHED OFF. Nothing is sent to a
  // guest right now. When testing ends, uncomment the block below - it never
  // sends to a blank address.
  /*
  if (guestEmail) {
    const guestHtml =
      '<div style="font-family:Arial,sans-serif;max-width:560px">' +
      '<h2>Your parking is confirmed</h2>' +
      '<p>Hello ' + esc_(d.name) + ',</p>' +
      '<p>Your vehicle has been added to the parking permit list at <b>' + esc_(CONFIG.PROPERTY_NAME) + '</b>. ' +
      'You can park without any problems during your stay.</p>' +
      detailsTable_(d) +
      '<p>If any of these details are wrong, please contact us straight away.</p>' +
      '<p>Kind regards,<br>' + esc_(CONFIG.BUSINESS_NAME) + '</p></div>';
    sendMail_(guestEmail,
      prefix + 'Your parking is confirmed - ' + CONFIG.PROPERTY_NAME, '',
      { name: CONFIG.BUSINESS_NAME, htmlBody: guestHtml });
  }
  */

  // To the shared inbox (always sent)
  const when = Utilities.formatDate(confirmedAt, CONFIG.TIMEZONE, 'dd/MM/yyyy HH:mm');
  const guestStatus = guestEmail
    ? 'Guest confirmations are switched off during testing, so the guest has NOT been emailed.'
    : 'This guest has no email address on file, so no confirmation can be sent to them.';
  const internalHtml =
    '<div style="font-family:Arial,sans-serif">' +
    '<p>Parking permit <b>confirmed</b> at ' + when + ' for:</p>' + detailsTable_(d) +
    '<p>' + guestStatus + '</p></div>';
  sendMail_(CONFIG.SHARED_INBOX,
    prefix + 'Permit confirmed - ' + d.reg + ' - ' + d.name, '',
    { name: CONFIG.BUSINESS_NAME, htmlBody: internalHtml });
}

function detailsTable_(d) {
  const row = function (label, value) {
    return '<tr><td style="padding:6px 12px;background:#f3f4f6"><b>' + label + '</b></td>' +
           '<td style="padding:6px 12px">' + esc_(value) + '</td></tr>';
  };
  let length = '';
  if (d.checkin instanceof Date && d.checkout instanceof Date) {
    // Covered from the check-in day to the check-out day inclusive
    const days = Math.round((d.checkout - d.checkin) / 864e5) + 1;
    if (days > 0) length = days + (days === 1 ? ' day' : ' days');
  }
  let html = '<table style="border-collapse:collapse;margin:12px 0">' +
    row('Guest name', d.name) +
    row('Vehicle registration', d.reg) +
    row('Vehicle', d.vehicle) +
    row('Check-in', fmtDate_(d.checkin)) +
    row('Check-out', fmtDate_(d.checkout)) +
    row('Permit length', length);
  if (d.notes) {
    html += '<tr><td colspan="2" style="padding:8px 12px;background:#fff7ed;color:#9a3412">' +
      '<b>Note:</b> ' + esc_(d.notes) + '</td></tr>';
  }
  return html + '</table>';
}

/* ============================================================
 * CONFIRM BUTTON (web page)
 * The email link opens a page with a second "Confirm" button.
 * This stops email security scanners from confirming by accident.
 * ============================================================ */
function doGet(e) {
  const token = (e && e.parameter && e.parameter.t) ? String(e.parameter.t) : '';
  const found = findByToken_(token);
  if (!found) return page_('<h2>Link not valid</h2><p>This confirm link is not recognised. Please contact the sender.</p>');

  const r = found.values;
  const status = String(r[COL.STATUS - 1]);
  if (status === 'Confirmed') {
    return page_('<h2>Already confirmed</h2><p>This permit was already confirmed. Thank you.</p>');
  }
  if (CONFIRMABLE_STATUSES.indexOf(status) === -1) {
    return page_('<h2>Not available</h2><p>This request cannot be confirmed right now. Please contact the sender.</p>');
  }

  const d = {
    name: String(r[COL.NAME - 1]), reg: String(r[COL.REG - 1]), vehicle: String(r[COL.VEHICLE - 1]),
    checkin: r[COL.CHECKIN - 1], checkout: r[COL.CHECKOUT - 1], notes: String(r[COL.NOTES - 1])
  };
  const safeToken = token.replace(/[^a-zA-Z0-9-]/g, '');
  const body =
    '<h2>Confirm parking permit</h2>' +
    '<p>Please check the details, add the vehicle to your permit list, then confirm.</p>' +
    detailsTable_(d) +
    '<button id="b" onclick="go()" style="background:#15803d;color:#fff;border:0;padding:12px 24px;' +
    'border-radius:6px;font-size:16px;font-weight:bold;cursor:pointer">Yes, permit has been added</button>' +
    '<p id="msg" style="font-weight:bold"></p>' +
    '<script>function go(){var b=document.getElementById("b");b.disabled=true;b.innerText="Confirming...";' +
    'google.script.run.withSuccessHandler(function(m){document.getElementById("msg").innerText=m;b.style.display="none";})' +
    '.withFailureHandler(function(){document.getElementById("msg").innerText="Something went wrong. Please try again.";' +
    'b.disabled=false;b.innerText="Yes, permit has been added";})' +
    '.confirmByToken("' + safeToken + '");}</script>';
  return page_(body);
}

// Called by the confirm page
function confirmByToken(token) {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const found = findByToken_(String(token));
    if (!found) return 'Link not valid.';
    const sheet = getSheet_();
    const r = found.values;
    const status = String(r[COL.STATUS - 1]);
    if (status === 'Confirmed') return 'Already confirmed. Thank you.';
    if (CONFIRMABLE_STATUSES.indexOf(status) === -1) return 'This request cannot be confirmed right now.';

    const now = new Date();
    sheet.getRange(found.row, COL.CONFIRMED_AT).setValue(now);
    setStatus_(sheet, found.row, 'Confirmed');
    SpreadsheetApp.flush();

    const d = {
      name: String(r[COL.NAME - 1]), reg: String(r[COL.REG - 1]), vehicle: String(r[COL.VEHICLE - 1]),
      checkin: r[COL.CHECKIN - 1], checkout: r[COL.CHECKOUT - 1], notes: String(r[COL.NOTES - 1])
    };
    try {
      sendConfirmationEmails_(d, String(r[COL.GUEST_EMAIL - 1]), now);
    } catch (err) {
      sheet.getRange(found.row, COL.STATUS).setValue('Confirmed - notify email failed');
    }
    return 'Thank you. Confirmed.';
  } finally {
    lock.releaseLock();
  }
}

/* ============================================================
 * HELPERS
 * ============================================================ */
// Sends one email. If SEND_FROM_ALIAS is on and the address is not allowed as a
// sender for the account running this script, it fails visibly (the row's
// Status shows an error) instead of quietly sending from a different address.
function sendMail_(to, subject, body, opts) {
  opts.replyTo = CONFIG.FROM_EMAIL;
  if (CONFIG.SEND_FROM_ALIAS) opts.from = CONFIG.FROM_EMAIL;
  GmailApp.sendEmail(to, subject, body, opts);
}

// Run this once from the editor to check the sender address is allowed.
// Look at the "Execution log" at the bottom of the editor for the result.
function checkSender() {
  const me = Session.getEffectiveUser().getEmail();
  if (!CONFIG.SEND_FROM_ALIAS) {
    Logger.log('Emails will be sent from: ' + me + ' (sender name "' + CONFIG.BUSINESS_NAME + '"), replies go to ' + CONFIG.FROM_EMAIL);
    return;
  }
  const aliases = GmailApp.getAliases();
  const ok = (me.toLowerCase() === CONFIG.FROM_EMAIL.toLowerCase()) ||
             aliases.map(function (a) { return a.toLowerCase(); }).indexOf(CONFIG.FROM_EMAIL.toLowerCase()) !== -1;
  Logger.log('Script is running as: ' + me);
  Logger.log('Send-as aliases on this account: ' + (aliases.length ? aliases.join(', ') : '(none)'));
  Logger.log(ok ? 'OK: ' + CONFIG.FROM_EMAIL + ' can be used as the sender.'
                : 'PROBLEM: ' + CONFIG.FROM_EMAIL + ' is NOT allowed as a sender for this account yet.');
}

function getSheet_() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) throw new Error('Sheet "' + CONFIG.SHEET_NAME + '" not found. Run setup first.');
  return sheet;
}

function setStatus_(sheet, rowNum, text) {
  sheet.getRange(rowNum, COL.STATUS).setValue(text);
}

function findByToken_(token) {
  if (!/^[a-zA-Z0-9-]{20,}$/.test(token)) return null;
  const sheet = getSheet_();
  const last = sheet.getLastRow();
  if (last < 2) return null;
  const tokens = sheet.getRange(2, COL.TOKEN, last - 1, 1).getValues();
  for (let i = 0; i < tokens.length; i++) {
    if (String(tokens[i][0]) === token) {
      const row = i + 2;
      return { row: row, values: sheet.getRange(row, 1, 1, HEADERS.length).getValues()[0] };
    }
  }
  return null;
}

function startOfToday_() {
  const s = Utilities.formatDate(new Date(), CONFIG.TIMEZONE, 'yyyy-MM-dd');
  const p = s.split('-');
  return new Date(Number(p[0]), Number(p[1]) - 1, Number(p[2]));
}

function fmtDate_(d) {
  return (d instanceof Date) ? Utilities.formatDate(d, CONFIG.TIMEZONE, 'EEE d MMM yyyy') : String(d);
}

function esc_(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function page_(bodyHtml) {
  return HtmlService.createHtmlOutput(
    '<div style="font-family:Arial,sans-serif;max-width:560px;margin:24px auto;padding:0 16px">' + bodyHtml + '</div>'
  ).setTitle('Parking permit').addMetaTag('viewport', 'width=device-width, initial-scale=1');
}
