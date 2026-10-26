"""
Clinical Treatment Protocols & Prescription Information Module
=============================================================
Provides evidence-based dermatological management guidelines,
first-line prescription measures, non-pharmacological care,
contraindications, and urgent referral signs for the 6 target conditions:

  1. Atopic Dermatitis
  2. Contact Dermatitis
  3. Eczema
  4. Scabies
  5. Seborrheic Dermatitis
  6. Tinea Corporis
"""

PROTOCOLS = {
    "Atopic Dermatitis": {
        "title": "Atopic Dermatitis",
        "category": "Chronic Relapsing Inflammatory Dermatosis",
        "description": "Characterized by pruritus, epidermal barrier dysfunction, and eczematous lesions on flexural surfaces.",
        "rx_first_line": [
            {
                "medication": "Hydrocortisone 1%–2.5% Cream / Ointment",
                "class_type": "Low-Potency Topical Corticosteroid (TCS)",
                "dosage": "Apply thin layer to affected face, neck, or intertriginous skin 1–2 times daily for up to 7–10 days during flares.",
                "note": "Preferred first-line for sensitive areas to prevent skin thinning."
            },
            {
                "medication": "Triamcinolone Acetonide 0.1% or Betamethasone Valerate 0.1%",
                "class_type": "Mid-Potency Topical Corticosteroid (TCS)",
                "dosage": "Apply to trunk and extremities 1–2 times daily for 1–2 weeks during acute inflammatory flare.",
                "note": "Taper frequency to intermittent or weekend maintenance as erythema subsides."
            },
            {
                "medication": "Tacrolimus 0.03%–0.1% Ointment (or Pimecrolimus 1% Cream)",
                "class_type": "Topical Calcineurin Inhibitor (TCI / Non-Steroidal)",
                "dosage": "Apply twice daily to lesions once acute flare is controlled.",
                "note": "Steroid-sparing maintenance; safe for long-term facial, periorbital, and neck usage."
            }
        ],
        "adjunct_otc": [
            {
                "medication": "Cetirizine 10mg or Hydroxyzine 25mg–50mg",
                "purpose": "Oral antipruritic / H1 antihistamine to reduce nocturnal scratching and improve sleep.",
                "dosage": "1 tablet at bedtime as needed."
            },
            {
                "medication": "Ceramide-Dominant Emollient Cream (e.g., Cetaphil, CeraVe, Aveeno Colloidal)",
                "purpose": "Epidermal lipid replenishment and skin barrier restoration.",
                "dosage": "Apply liberally at least 2–3 times daily and within 3 minutes of bathing ('soak and seal')."
            }
        ],
        "non_pharma_measures": [
            "Bathing Protocol: Take brief (<10 min) lukewarm showers or baths; avoid hot water which triggers pruritus.",
            "Soak & Seal: Pat skin lightly with a clean towel (do not rub) and immediately apply thick emollient while skin is damp.",
            "Clothing & Fabrics: Wear loose, breathable 100% cotton clothing. Avoid wool, synthetic polyesters, and abrasive tags.",
            "Environmental Triggers: Use fragrance-free, dye-free laundry detergents. Maintain indoor humidity around 40%–50%."
        ],
        "contraindications": [
            "Do NOT use high-potency topical corticosteroids continuously for >2 weeks without physician review.",
            "Avoid topical antihistamines (e.g., diphenhydramine cream) as they carry a high risk of contact allergic sensitization.",
            "Do not abruptly stop high-potency steroids; taper gradually to prevent rebound exacerbation."
        ],
        "urgent_referral": [
            "Sudden emergence of punched-out, clustered vesicular blisters with fever (suspicion of Eczema Herpeticum).",
            "Signs of secondary bacterial superinfection: honey-colored crusting, purulent exudate, pustules, or localized heat/redness.",
            "Severe erythroderma covering >90% of total body surface area."
        ]
    },

    "Contact Dermatitis": {
        "title": "Contact Dermatitis (Allergic & Irritant)",
        "category": "Exogenous Cutaneous Inflammatory Reaction",
        "description": "Triggered by direct skin contact with exogenous allergens (e.g., nickel, urushiol, fragrances) or irritants (detergents, solvents).",
        "rx_first_line": [
            {
                "medication": "Clobetasol Propionate 0.05% or Triamcinolone 0.1% Cream",
                "class_type": "High-to-Mid Potency Topical Corticosteroid",
                "dosage": "Apply thinly to active vesicular or erythematous plaques twice daily for 7–14 days.",
                "note": "Use mid-potency on body/limbs; use low-potency (Desonide 0.05%) on face or flexures."
            },
            {
                "medication": "Oral Prednisone Taper (Severe Cases Only)",
                "class_type": "Systemic Corticosteroid",
                "dosage": "40–60 mg/day tapered over 14–21 days under strict physician supervision.",
                "note": "Indicated when >20% body surface area is involved or in severe facial/eyelid edema (e.g., poison ivy)."
            }
        ],
        "adjunct_otc": [
            {
                "medication": "Calamine Lotion or Pramoxine 1% Cream",
                "purpose": "Topical antipruritic soothing agent for oozing or blistered lesions.",
                "dosage": "Apply to itchy areas 3–4 times daily."
            },
            {
                "medication": "Fexofenadine 180mg or Loratadine 10mg",
                "purpose": "Non-sedating oral second-generation antihistamine for daytime pruritus.",
                "dosage": "1 tablet once daily."
            }
        ],
        "non_pharma_measures": [
            "Culprit Identification: Strictly identify and cease contact with the inciting allergen/irritant (cosmetics, plants, metals).",
            "Burow's Solution Compresses: Apply cool compresses with aluminum acetate (1:40 dilution) for 15 minutes 3 times daily to dry weeping vesicles.",
            "Barrier Protection: Wear nitrile gloves for wet housework; wash contaminated skin and garments immediately after suspected exposure."
        ],
        "contraindications": [
            "Avoid topical neomycin, bacitracin, or topical benzocaine—these are potent contact allergens that worsen the rash.",
            "Avoid short oral steroid bursts (<7 days) for allergic phytodermatitis, as severe rebound rebound dermatitis frequently ensues."
        ],
        "urgent_referral": [
            "Significant facial, periorbital, or genital swelling impairing vision or breathing.",
            "Spreading cellulitis characterized by ascending erythema, warmth, severe pain, or systemic fever."
        ]
    },

    "Eczema": {
        "title": "Eczema (Nummular / Dyshidrotic / General)",
        "category": "Pruritic Cutaneous Dermatitis Spectrum",
        "description": "Presents as coin-shaped (nummular) plaques, tapioca-like vesicles on hands/feet (dyshidrosis), or generalized xerotic dermatitis.",
        "rx_first_line": [
            {
                "medication": "Mometasone Furoate 0.1% Ointment",
                "class_type": "Mid-to-High Potency Topical Corticosteroid",
                "dosage": "Apply once daily at bedtime to active plaques for 2–3 weeks.",
                "note": "Ointment base provides superior occlusion and hydration over dry, crusted eczema."
            },
            {
                "medication": "Clobetasol Propionate 0.05% Ointment (Dyshidrotic Eczema)",
                "class_type": "Super-High Potency Topical Corticosteroid",
                "dosage": "Apply twice daily under cotton gloves or occlusion on thick palmar/plantar skin for 10–14 days.",
                "note": "Palms and soles require high potency due to stratum corneum thickness."
            }
        ],
        "adjunct_otc": [
            {
                "medication": "Urea 10%–20% or Ammonium Lactate 12% Cream",
                "purpose": "Topical keratolytic and natural humectant for thick, hyperkeratotic, lichenified skin.",
                "dosage": "Apply twice daily between steroid applications."
            },
            {
                "medication": "Levocetirizine 5mg or Diphenhydramine 25mg",
                "purpose": "Oral antipruritic to interrupt the chronic scratch-itch cycle.",
                "dosage": "1 tablet at bedtime."
            }
        ],
        "non_pharma_measures": [
            "Wet Wrap Therapy: After applying moisturizer or mild steroid ointment, wrap the limb in a damp cotton layer followed by a dry outer layer overnight.",
            "Frequent Hand Barrier Care: Use soap-free lipid syndets; dry hands thoroughly and immediately apply petrolatum-based barrier ointment.",
            "Avoid Harsh Sanitizers: Alcohol-based rubs can provoke stinging and fissure propagation during active eczematous flare."
        ],
        "contraindications": [
            "Do not scrub crusts or scales aggressively with loofahs or brushes; causes mechanical microtrauma.",
            "Do not apply super-potent steroids (Clobetasol) to the face, groin, or axillae."
        ],
        "urgent_referral": [
            "Deep painful fissures that develop yellow purulence or bleeding (possible secondary MRSA colonization).",
            "Rapid flare with systemic chills, fever, or painful regional lymphadenopathy."
        ]
    },

    "Scabies": {
        "title": "Scabies Infestation",
        "category": "Ectoparasitic Dermatological Infestation",
        "description": "Highly contagious parasitic infestation caused by Sarcoptes scabiei hominis burrowing into the stratum corneum.",
        "rx_first_line": [
            {
                "medication": "Permethrin 5% Dermal Cream",
                "class_type": "First-Line Topical Scabicide (Neurotoxic to Mites)",
                "dosage": "Apply thoroughly from jawline to soles of feet (including finger webs, under nails, and genitals). Leave on for 8–14 hours (overnight), then wash off thoroughly. MUST repeat exact application in 7–10 days.",
                "note": "The Day 7 repeat dose is essential to kill newly hatched nymphs before they mature."
            },
            {
                "medication": "Oral Ivermectin 200 µg/kg",
                "class_type": "Systemic Anti-Parasitic (Oral Scabicide)",
                "dosage": "Single oral dose with food, repeated strictly 7 to 14 days later.",
                "note": "Preferred for institutional outbreaks, elderly patients, severe crusted (Norwegian) scabies, or topical treatment failures."
            }
        ],
        "adjunct_otc": [
            {
                "medication": "Hydrocortisone 1% Cream (Post-Scabetic Care)",
                "purpose": "Soothes persistent allergic dermatitis AFTER completed mite eradication.",
                "dosage": "Apply twice daily to itchy papules for 1–2 weeks."
            },
            {
                "medication": "Oral Antihistamines (Hydroxyzine 25mg / Cetirizine 10mg)",
                "purpose": "Alleviates intense nocturnal hypersensitivity itch.",
                "dosage": "1 tablet before sleep."
            }
        ],
        "non_pharma_measures": [
            "Simultaneous Household Treatment: ALL household members, bedroom contacts, and sexual partners MUST be treated simultaneously, even if asymptomatic.",
            "Hot Wash Environmental Decontamination: Wash all bed linens, towels, and clothing worn in the past 4 days in hot water (>50°C / 122°F) and cycle through high-heat dryer for 30 minutes.",
            "Airtight Storage: Seal non-washable items (pillows, coats, soft toys) in airtight plastic bags for 72 hours (mites perish away from human skin).",
            "Nail Hygiene: Clip fingernails short and brush permethrin cream under the free edges to eliminate subungual reservoirs."
        ],
        "contraindications": [
            "Do NOT repeat Permethrin daily or continuously—itching typically persists for 2–4 weeks post-treatment due to dead mite antigens (post-scabetic itch).",
            "Do NOT use Lindane 1% lotion (high risk of neurotoxicity and seizures, especially in children).",
            "Oral Ivermectin is contraindicated in children <15 kg and during pregnancy."
        ],
        "urgent_referral": [
            "Widespread thick, crusted, hyperkeratotic fissures (Crusted / Norwegian Scabies—extreme contagion risk).",
            "Development of secondary bacterial impetigo or cellulitis from intense nocturnal excoriation."
        ]
    },

    "Seborrheic Dermatitis": {
        "title": "Seborrheic Dermatitis",
        "category": "Chronic Superficial Fungal-Inflammatory Condition",
        "description": "Inflammatory response associated with Malassezia yeast proliferation on sebum-rich cutaneous areas (scalp, eyebrows, nasolabial folds, chest).",
        "rx_first_line": [
            {
                "medication": "Ketoconazole 2% Cream or Foaming Gel",
                "class_type": "Topical Imidazole Antifungal",
                "dosage": "Apply to affected facial, ear, or chest areas twice daily for 2–4 weeks until clinical resolution, then 1–2 times weekly for maintenance.",
                "note": "Reduces Malassezia yeast colonization without steroid-related side effects."
            },
            {
                "medication": "Ketoconazole 2% or Ciclopirox 1% Shampoo",
                "class_type": "Medicated Antifungal Shampoo (Scalp & Beard)",
                "dosage": "Apply to wet scalp/beard, lather, leave in place for full 5 minutes before rinsing. Use 2–3 times per week.",
                "note": "5-minute contact time is critical for active drug penetration into hair follicles."
            },
            {
                "medication": "Desonide 0.05% or Hydrocortisone 1% (Short-Term Only)",
                "class_type": "Low-Potency Topical Corticosteroid",
                "dosage": "Apply sparingly once daily for 3–5 days maximum to rapidly quell severe acute erythema.",
                "note": "Discontinue as soon as acute burning/redness improves."
            }
        ],
        "adjunct_otc": [
            {
                "medication": "Selenium Sulfide 2.5% or Zinc Pyrithione 1%–2% Shampoo",
                "purpose": "Keratoregulating and antifungal scalp wash.",
                "dosage": "Alternate with Ketoconazole shampoo on non-treatment days."
            },
            {
                "medication": "Salicylic Acid 2%–3% Solution / Mineral Oil",
                "purpose": "Softens and loosens thick, greasy, adherent scalp scales (cradle cap or adult plaque).",
                "dosage": "Apply 1 hour before shampooing."
            }
        ],
        "non_pharma_measures": [
            "Sebum Regulation: Wash face and scalp regularly with gentle, fragrance-free, oil-free syndet cleansers.",
            "Avoid Heavy Pomades: Avoid greasy hair waxes, oils, and occlusive face balms that foster Malassezia proliferation.",
            "Sun Exposure: Brief, moderate natural sunlight exposure often helps improve lesions through mild UV suppression of yeast."
        ],
        "contraindications": [
            "STRICTLY AVOID high-potency topical corticosteroids on the face (causes perioral dermatitis, steroid rosacea, and skin atrophy).",
            "Avoid scratching or picking adherent scales; increases the risk of secondary staphylococcal folliculitis."
        ],
        "urgent_referral": [
            "Severe facial eruption unresponsive to 4 weeks of topical antifungal therapy.",
            "Severe, widespread exfoliative erythroderma or suspicion of underlying immunocompromise."
        ]
    },

    "Tinea Corporis": {
        "title": "Tinea Corporis (Ringworm)",
        "category": "Superficial Dermatophytic Fungal Infection",
        "description": "Fungal infection of keratinized stratum corneum (Trichophyton or Microsporum spp.) presenting as annular, well-demarcated scaling plaques with central clearing.",
        "rx_first_line": [
            {
                "medication": "Terbinafine 1% Cream (First-Line Fungicidal Allylamine)",
                "class_type": "Topical Fungicidal Allylamine",
                "dosage": "Apply once or twice daily to the lesion PLUS a 2–3 cm margin of normal skin for 1–2 weeks.",
                "note": "Superior cure rates and lower relapse compared to fungistatic azoles."
            },
            {
                "medication": "Clotrimazole 1% or Miconazole 2% Cream",
                "class_type": "Topical Imidazole Antifungal",
                "dosage": "Apply twice daily extending 2 cm beyond the active outer border for 2–4 weeks.",
                "note": "Continue application for a full 7 days after visible clinical clearance to prevent recurrence."
            },
            {
                "medication": "Oral Terbinafine 250mg Daily (Widespread / Refractory Cases)",
                "class_type": "Systemic Antifungal",
                "dosage": "250 mg once daily with food for 2–4 weeks (requires physician monitoring of liver transaminases).",
                "note": "Indicated when multiple widespread body regions, tinea incognito, or immunosuppression are present."
            }
        ],
        "adjunct_otc": [
            {
                "medication": "Tolnaftate 1% Powder or Spray",
                "purpose": "Absorbs excess moisture and suppresses fungal growth in skin folds.",
                "dosage": "Apply to shoes, groin, or body folds daily."
            }
        ],
        "non_pharma_measures": [
            "Keep Skin Clean and Dry: Dermatophytes thrive in humid, macerated environments; dry thoroughly after bathing.",
            "Hygiene & Towel Separation: Use a separate clean towel for the infected area and do not share towels or clothing.",
            "Veterinary Check: If you have domestic pets (cats, dogs), have a veterinarian inspect them for circular patches of hair loss (frequent zoophilic source).",
            "Gym / Sports Caution: Disinfect athletic mats and wear loose, sweat-wicking synthetic or cotton garments."
        ],
        "contraindications": [
            "NEVER USE TOPICAL CORTICOSTEROIDS ALONE OR IN MONOTHERAPY: Steroids suppress local immunity, allowing fungus to proliferate unchecked and transform into 'Tinea Incognito' (loss of ring border, deep invasive pustules).",
            "Avoid combination steroid-antifungal creams (e.g., Betamethasone + Clotrimazole / Lotrisone) as they cause high relapse rates, cutaneous atrophy, and diagnostic confusion."
        ],
        "urgent_referral": [
            "Extensive, rapidly spreading plaques covering large areas of the trunk and limbs.",
            "Deep, boggy, purulent inflammatory masses (Majocchi's granuloma / kerion-like reaction) requiring systemic therapy."
        ]
    }
}


def get_protocol(disease_name):
    """
    Retrieve clinical management protocol for a predicted condition.
    Returns None if disease_name is not in the recognized dictionary.
    """
    if not disease_name:
        return None
    return PROTOCOLS.get(disease_name.strip())
