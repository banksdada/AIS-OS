#!/usr/bin/env python3
"""Generate the Beauty Booked Up Canva image prompt bank."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "projects" / "beautybookedup" / "canva-image-prompts.txt"

STYLE = (
    "High-key editorial beauty-business photography for Beauty Booked Up, a UK salon marketing service. "
    "Bright warm ivory studio or salon setting, soft natural daylight, gentle shadows, raspberry and blush accents, "
    "light oak and champagne details. Photorealistic, premium but approachable, natural skin texture, polished commercial photography."
)

COMMON = (
    "Leave generous negative space for text overlay. No words, no logos, no watermarks, no fake brand names, "
    "no cheesy stock poses, no heavy filters, no dark moody lighting, no distorted hands."
)

SCENES = {
    "Beauty business admin and bookings": [
        "A beautician at a clean salon desk reviewing online bookings on a tablet, calm and focused.",
        "A salon owner ticking off a printed appointment diary beside a laptop and a cup of tea.",
        "A beauty therapist smiling while checking a mobile booking confirmation in a bright treatment room.",
        "A tidy salon reception with a tablet stand, appointment cards and a small vase of pale flowers.",
        "A beauty business owner writing a weekly content plan beside a calendar and a laptop.",
        "A lash tech's hands entering a new client into a digital booking system on a phone.",
        "A salon desk with a clean appointment book, raspberry pen and soft ivory background.",
        "A beautician sorting appointment cards into a simple colour-coded system.",
        "A calm beauty studio morning with a therapist opening the door ready for the first client.",
        "A mobile beauty therapist checking the day's route on a phone in a bright hallway.",
        "A salon owner reviewing a client follow-up message on a laptop, warm and unhurried.",
        "A beauty professional comparing a paper diary and a digital calendar at a tidy desk.",
        "Close-up of hands using a stylus to move appointments on a tablet calendar.",
        "A friendly reception moment with a client checking in at a bright beauty salon desk.",
        "A beauty business owner at a minimal desk with a notebook labelled only with blank tabs, no readable text.",
        "A calm empty treatment room ready for the next appointment, fresh towels folded neatly.",
        "A therapist writing a thank-you card after an appointment, no readable text on the card.",
        "A salon owner looking at a tablet showing a full diary, cropped so the screen has no readable text.",
        "A beauty professional organising client record cards in a warm, tidy studio.",
        "A soft editorial shot of a booking bell, clean desk surface and raspberry accent in the background.",
    ],
    "Lash tech and lash studio": [
        "A lash tech carefully applying classic lashes to a relaxed client, elegant hands in sharp detail.",
        "A lash artist mapping lashes with a tidy workstation and soft raspberry accents.",
        "A finished lash set close-up with natural texture and a calm, healthy look.",
        "A lash tech preparing a clean lash tray and tools in a bright studio.",
        "A client looking in a mirror after a lash appointment, soft smile and natural lighting.",
        "A lash artist adjusting a client's lashes with precision and gentle focus.",
        "A bright lash studio treatment bed with fresh linen and a neat tool trolley.",
        "Close-up of a lash wand and tweezers arranged on an ivory surface.",
        "A lash tech explaining aftercare to a client, both relaxed and professional.",
        "A beauty therapist applying lashes in a clean Manchester lash studio.",
        "A lash artist's hands working in soft daylight, shallow depth of field.",
        "A calm client portrait with beautiful lashes and natural skin texture.",
        "A lash studio shelf with neatly arranged lash trays, no readable labels.",
        "A lash tech setting up a treatment room before a client arrives.",
        "A side-profile shot of a lash application in progress, calm and precise.",
        "A lash artist smiling at a finished set in a bright mirror.",
        "A clean lash extension kit laid out on a warm ivory surface.",
        "A lash tech checking the final result from different angles.",
        "A Wigan lash studio scene with a client settling onto the treatment bed.",
        "A premium editorial close-up of lashes, skin and soft linen with raspberry detail.",
    ],
    "Nail tech and nail studio": [
        "A nail tech finishing a neat manicure at a bright salon station, hands and tools in sharp detail.",
        "A client showing freshly shaped nails in soft daylight, elegant and natural.",
        "A nail artist applying a smooth polish coat with careful concentration.",
        "A tidy nail desk with files, cuticle tools and warm ivory surfaces.",
        "Close-up of a BIAB manicure with a glossy finish and natural nail shape.",
        "A nail tech preparing a clean workstation before a client appointment.",
        "A client relaxing while their nails soak in a bright treatment room.",
        "A nail artist selecting polish shades from a clean raspberry-accented display.",
        "A Manchester nail salon scene with a calm client and professional nail tech.",
        "Hands holding a finished manicure against soft linen and pale blush background.",
        "A nail tech checking cuticle detail with precision and soft studio lighting.",
        "A nail salon shelf with polished jars and fresh towels, no readable labels.",
        "A client laughing gently during a nail appointment, natural and unforced.",
        "A nail file and buffer arranged neatly on an ivory work surface.",
        "A nail artist applying a neutral polish with a steady hand.",
        "A finished set of almond-shaped nails photographed in warm daylight.",
        "A Wigan nail studio with a tidy chair, clean tools and raspberry accent.",
        "A nail tech offering a client a colour choice, no readable text on samples.",
        "A close-up of a cuticle being shaped with professional tools.",
        "A serene nail salon detail shot with soft shadows and premium editorial styling.",
    ],
    "Brow artist and brow studio": [
        "A brow artist shaping brows with precision in a bright, calm treatment room.",
        "A client viewing neatly shaped brows in a handheld mirror, natural smile.",
        "A brow lamination appointment in progress with soft daylight and clean linen.",
        "A tidy brow station with brushes, tint bowls and warm ivory surfaces.",
        "Close-up of brow mapping lines on a client with natural skin texture.",
        "A brow artist explaining aftercare to a relaxed client.",
        "A Wigan brow studio with a clean treatment chair and raspberry detail.",
        "A brow tint being applied carefully in a bright professional setting.",
        "A finished brow shape photographed in soft, even light.",
        "A brow artist's hands arranging tools on a clean trolley.",
        "A calm client portrait with beautifully groomed brows and no heavy makeup.",
        "A brow studio mirror with a tidy workspace reflected softly.",
        "A Manchester brow artist working gently with a client.",
        "A close-up of brow brushes and a clean palette on an ivory table.",
        "A client relaxing before a brow treatment, fresh towels nearby.",
        "A brow artist checking symmetry from a flattering angle.",
        "A clean brow treatment room ready for the next appointment.",
        "A side-profile brow detail shot with warm, natural tones.",
        "A brow artist smiling softly after completing a treatment.",
        "A premium editorial brow close-up with blush and raspberry accents.",
    ],
    "Hairdressers and hair salons": [
        "A hairdresser in a light modern salon, client in chair, natural conversation, relaxed premium feel.",
        "A stylist blow-drying a client's hair in a bright Wigan salon.",
        "A hairdresser sectioning hair with precision and calm focus.",
        "A finished glossy hairstyle photographed in soft daylight.",
        "A clean salon station with brushes, scissors and warm ivory surfaces.",
        "A client smiling at their reflection after a hair appointment.",
        "A hairdresser mixing colour in a bright professional salon.",
        "A stylist checking the finish of a haircut from behind the chair.",
        "A Manchester hair salon with light oak furniture and raspberry accents.",
        "Close-up of a hairdresser's hands using a comb and scissors.",
        "A client having a fringe trimmed in a calm, modern salon.",
        "A hair salon mirror with soft reflections and tidy workstations.",
        "A hairdresser offering a client a mirror at the end of an appointment.",
        "A clean cape and fresh towels ready for a salon client.",
        "A stylist applying finish spray with gentle, professional motion.",
        "A relaxed salon conversation between hairdresser and client.",
        "A haircut in progress with natural texture and realistic hair detail.",
        "A bright salon shelf with neatly arranged products, no readable labels.",
        "A hairdresser adjusting a client's style in a flattering angle.",
        "A premium editorial salon portrait with soft blush and ivory tones.",
    ],
    "African hair, braids, locs and wigs": [
        "An African hair braider working on braids with beautiful texture detail, warm and respectful representation.",
        "A stylist installing locs in a bright, modern North West salon.",
        "Close-up of freshly braided hair with neat parting and natural shine.",
        "A client admiring a loc style in a salon mirror, calm and confident.",
        "A braider preparing hair sections with precision and care.",
        "A wig stylist fitting a client in a clean, bright treatment room.",
        "A protective style being finished with soft daylight and elegant composition.",
        "A Manchester braiding studio with warm textures and raspberry accents.",
        "A stylist detangling textured hair gently before braiding.",
        "A client portrait with beautiful braids and natural skin texture.",
        "A braider's hands creating neat parts on a clean ivory background.",
        "A loc retwist appointment in progress, calm and professional.",
        "A wig on a stand in a bright salon, premium editorial styling.",
        "A stylist discussing a braid pattern with a client, no readable references.",
        "Close-up of braided hair ends being finished carefully.",
        "A Wigan African hair studio with a tidy chair and warm welcoming feel.",
        "A client relaxing during a long braiding appointment.",
        "A stylist checking the shape of a loc style from the side.",
        "A clean product shelf with textured hair care jars, no readable labels.",
        "A respectful editorial portrait celebrating natural hair texture.",
        "A braiding session with clean linen, soft shadows and light oak details.",
        "A stylist adding finishing detail to a protective style.",
        "A textured hair close-up with beautiful definition and soft raspberry backdrop.",
        "A confident client after a loc or braid appointment, natural and unforced.",
    ],
    "Aestheticians and skin clinics": [
        "An aesthetician preparing a treatment room with clean linen and soft daylight.",
        "A client relaxing before a facial in a calm, bright skin clinic.",
        "Aesthetician hands applying a mask with gentle precision.",
        "A tidy treatment trolley with professional skincare bottles, no readable labels.",
        "A Manchester aesthetics clinic with ivory walls and raspberry accents.",
        "A client sitting upright after a treatment, natural glow and calm expression.",
        "A close-up of a cleanser bottle and folded towels on a clean surface.",
        "An aesthetician explaining a treatment plan to a client, warm and professional.",
        "A soft portrait of a client with healthy-looking skin and no heavy retouching.",
        "A treatment bed ready with fresh towels and a gentle blush throw.",
        "Aesthetician checking skin with a magnifying lamp in soft light.",
        "A Wigan skin clinic reception with a clean desk and calm atmosphere.",
        "A client having a gentle facial massage in a bright clinic.",
        "A premium skincare detail shot with glass, ivory and champagne tones.",
        "An aesthetician washing hands before a treatment, professional and reassuring.",
        "A client viewing their reflection after a facial, calm and pleased.",
        "A clean clinic corner with a plant, stool and tidy product display.",
        "Aesthetician applying serum with elegant, careful hands.",
        "A quiet consultation moment between aesthetician and client.",
        "A beauty clinic hero image with generous empty space for a headline.",
    ],
    "Mobile beauty therapists": [
        "A mobile beauty therapist carrying a tidy kit bag into a bright client home.",
        "A therapist setting up a treatment in a calm living room with soft daylight.",
        "A mobile lash tech preparing a clean portable workstation.",
        "A beauty therapist unpacking fresh towels from a compact case.",
        "A client relaxing at home before a mobile beauty appointment.",
        "A mobile nail tech working at a neat table in a bright home setting.",
        "A therapist's hands arranging tools in a portable kit, warm ivory tones.",
        "A mobile beauty van parked outside a Wigan home, tasteful and unbranded.",
        "A therapist checking appointment details on a phone before entering a client home.",
        "A clean pop-up treatment station in a Manchester apartment.",
        "A mobile aesthetician setting up a small treatment lamp and tidy trolley.",
        "A client smiling after a mobile brow appointment in their own home.",
        "A compact beauty kit with raspberry accents and organised compartments.",
        "A therapist carrying a professional case through a light hallway.",
        "A home treatment scene with fresh linen, soft shadows and calm composition.",
        "A mobile beauty therapist saying goodbye to a client at the door.",
    ],
    "Instagram, DMs and social media": [
        "A beauty business owner photographing a finished treatment for Instagram in bright daylight.",
        "A salon owner replying to client messages on a phone at a tidy desk.",
        "A lash tech creating a content shot with a raspberry backdrop.",
        "A nail tech holding a phone showing a draft post, no readable text.",
        "A beauty salon phone on a stand beside fresh towels and a clean work surface.",
        "A therapist filming a short salon tip in a bright treatment room.",
        "A beauty business owner planning Instagram highlights with a blank content board.",
        "A client sending a booking enquiry on a phone, hands only, no readable text.",
        "A salon desk with a phone, ring light and warm ivory background.",
        "A beauty professional sorting saved replies on a laptop, screen blurred.",
        "A brow artist taking a close-up content photo of a finished brow shape.",
        "A hairdresser filming a quick transformation with a phone in a modern salon.",
        "A flat-lay of phone, notebook and raspberry pen on an ivory desk.",
        "A beauty brand content corner with clean backdrop and soft daylight.",
        "A salon owner reviewing a weekly social plan, no readable text on pages.",
        "A client’s hands typing a message to a beauty business, elegant and natural.",
        "A mobile therapist photographing their kit for social media.",
        "A lash studio shelf used as a clean background for a content shoot.",
        "A beauty professional editing a photo on a tablet, screen blurred.",
        "A calm, premium social media planning scene with blush and champagne accents.",
    ],
    "Google, reviews and local visibility": [
        "A beauty salon owner checking local search results on a laptop, screen blurred.",
        "A client leaving a review on a phone after a treatment, no readable text.",
        "A salon owner celebrating a five-star review with a quiet smile.",
        "A bright Wigan beauty salon exterior with clean windows and no signage text.",
        "A Manchester hair salon reception with a calm, professional welcome area.",
        "A therapist reading a kind client message on a phone, warm expression.",
        "A laptop and notebook showing a local SEO checklist, no readable text.",
        "A beauty business owner comparing map pins on a tablet, screen blurred.",
        "A clean salon desk with a small card stand, no readable text.",
        "A client walking into a bright beauty studio, welcoming atmosphere.",
        "A salon owner reviewing online visibility notes at a tidy desk.",
        "A phone showing a Google-style review stars interface, no readable words.",
        "A beauty therapist holding a thank-you card after a great appointment.",
        "A local high-street beauty salon scene with soft morning light.",
        "A business owner updating a salon profile on a laptop, screen blurred.",
        "A premium editorial shot of a salon door opening to a bright, calm interior.",
    ],
    "AI, automation and client experience": [
        "A salon owner using a simple automation dashboard on a laptop, screen blurred.",
        "A beauty business owner drafting an automated reply on a phone, no readable text.",
        "A client receiving a friendly appointment reminder on a phone.",
        "A tidy desk with laptop, notebook and raspberry accent representing calm automation.",
        "A therapist reviewing automated follow-ups on a tablet, screen blurred.",
        "A salon calendar and phone placed side by side on an ivory desk.",
        "A beauty business owner mapping a simple client journey on paper, no readable text.",
        "A client checking a booking link on a phone in a bright home setting.",
        "A salon owner reading a weekly automation summary, calm and focused.",
        "A laptop with a blurred chatbot window beside fresh flowers and a notebook.",
        "A beauty professional scheduling a reminder on a phone, warm daylight.",
        "A clean workflow diagram drawn as abstract shapes on paper, no readable text.",
        "A client replying to a reminder message, hands only, no readable text.",
        "A salon desk with phone, tablet and appointment cards arranged neatly.",
        "A business owner relaxing because admin is under control, bright studio setting.",
        "A premium editorial image of technology and beauty working together, soft and uncluttered.",
    ],
    "Wigan and Manchester local editorial": [
        "A bright beauty studio interior with subtle Wigan character and no readable signage.",
        "A Manchester salon street scene in soft daylight, tasteful and unbranded.",
        "A Wigan high street beauty salon doorway with warm light and clean lines.",
        "A client walking into a Manchester lash studio, relaxed and confident.",
        "A calm salon interior with light oak, ivory and raspberry accents.",
        "A beauty therapist in a North West salon greeting a client warmly.",
        "A modern Wigan treatment room with fresh linen and soft daylight.",
        "A Manchester hair salon chair by a bright window, no readable posters.",
        "A quiet high-street café table with a notebook and phone, representing local planning.",
        "A beauty business owner looking out of a salon window in Wigan.",
        "A clean salon reception with a local editorial feel and no readable text.",
        "A client leaving a Manchester beauty appointment with a natural smile.",
        "A North West salon shelf with neutral products and raspberry detail.",
        "A bright treatment room with a view of a familiar high street, no landmarks requiring accuracy.",
        "A Wigan beauty studio desk with appointment cards and warm daylight.",
        "A premium editorial local salon portrait with generous negative space.",
    ],
    "Clean backgrounds and text-overlay heroes": [
        "A warm ivory salon desk with a raspberry pen and soft shadow, lots of empty space.",
        "A blush backdrop with a small champagne tray and clean negative space.",
        "A folded towel stack on an ivory surface with a raspberry ribbon detail.",
        "A soft salon interior background with no people, clean and uncluttered.",
        "A light oak tabletop with a small vase and pale flowers, editorial style.",
        "A minimalist treatment bed corner with fresh linen and soft daylight.",
        "A clean blush and ivory flat-lay with beauty tools arranged neatly.",
        "A raspberry accent wall blurred gently behind a warm ivory foreground.",
        "A calm beauty desk with a closed notebook and phone, no readable text.",
        "A soft-focus salon shelf with neutral bottles and no readable labels.",
        "A champagne and blush still life with generous space for a headline.",
        "A bright empty studio corner with clean lines and a premium feel.",
        "A neutral beauty flat-lay with tweezers, brush and small mirror.",
        "A warm ivory background with gentle raspberry shadow and no objects in the centre.",
        "A clean editorial background for a blog hero, calm and feminine but not childish.",
        "A minimal salon detail with light oak, soft linen and a raspberry accent.",
    ],
}


def prompt_text(index, category, scene, aspect="16:9"):
    ratio = "16:9 landscape hero, with a matching 1:1 square crop" if aspect == "16:9" else "1:1 square"
    return (
        f"PROMPT {index:03d} — {category}\n"
        f"Paste into Canva Magic Media:\n"
        f"{STYLE} {scene} Style: high-key editorial, photorealistic, premium but approachable. "
        f"Mood: calm, confident, welcoming. Lighting: soft natural daylight with gentle shadows. "
        f"Colour palette: warm ivory, blush, raspberry, light oak, champagne. "
        f"Composition: {ratio}, generous empty space for text overlay. {COMMON}\n"
    )


def main():
    blocks = [
        "Beauty Booked Up — Canva image prompt bank\n"
        "Use: paste one prompt into Canva Magic Media. Generate a 16:9 hero and a 1:1 crop where possible.\n"
        "Download approved images into the shared Google Drive image dump and tag them in the image manifest.\n"
        "These are illustrative prompts, not client work or testimonials.\n"
    ]
    index = 1
    for category, scenes in SCENES.items():
        blocks.append(f"\n=== {category} ===\n")
        for scene in scenes:
            blocks.append(prompt_text(index, category, scene))
            index += 1
    OUT_PATH.write_text("\n".join(blocks))
    print(f"Wrote {index - 1} prompts to {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
