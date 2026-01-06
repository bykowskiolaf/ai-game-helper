ProxiHUD = {}
ProxiHUD.name = "ProxiHUD_Bridge"

function ProxiHUD.OnPlayerUnloaded()
    local function GetFullInventory()
        local inv = {}

        local qualityNames = {
            [0]="Trash", [1]="Normal", [2]="Fine", [3]="Superior", [4]="Epic", [5]="Legendary"
        }

        local function ScanBag(bagId, locationTag)
            local bagCache = SHARED_INVENTORY:GenerateFullSlotData(nil, bagId)

            for _, data in pairs(bagCache) do
                -- FIX: Generate a fresh, valid Item Link using the ID and Slot
                -- The default 'data.itemLink' is often insufficient for deep queries.
                local link = GetItemLink(data.bagId, data.slotIndex)

                -- 1. Quality
                local quality = data.quality or 1
                local qualityStr = qualityNames[quality] or "Unknown"

                -- 2. Trait (Fixed)
                local traitType = GetItemLinkTraitInfo(link)
                local traitStr = "None"
                if traitType and traitType > 0 then
                    -- Get the in-game string for this trait ID (e.g., "Divines")
                    traitStr = GetString("SI_ITEMTRAITTYPE", traitType)
                end

                -- 3. Set Name (Fixed)
                local hasSet, setName, _, _, _ = GetItemLinkSetInfo(link, false)
                if not hasSet or setName == "" then
                    setName = "No Set"
                else
                    -- Clean up name casing just in case
                    setName = zo_strformat("<<1>>", setName)
                end

                -- 4. Value
                local value = GetItemLinkValue(link, false)

                -- Format: "Mother's Sorrow Inferno Staff (x1) [Bag] {Epic} <Divines> (Set: Mother's Sorrow) $50g"
                local entry = string.format("%s (x%d) [%s] {%s} <%s> (Set: %s) $%dg",
                    zo_strformat("<<1>>", data.name), -- Proper capitalization
                    data.stackCount,
                    locationTag,
                    qualityStr,
                    traitStr,
                    setName,
                    value
                )

                table.insert(inv, entry)
            end
        end

        ScanBag(BAG_BACKPACK, "Bag")
        ScanBag(BAG_BANK, "Bank")

        return inv
    end

    local function GetActiveQuests()
        local quests = {}
        for i = 1, GetNumJournalQuests() do
            local name = GetJournalQuestInfo(i)
            if name and name ~= "" then
                table.insert(quests, name)
            end
        end
        return quests
    end

    local function GetSkills()
        local skills = {}

        local function ScanBar(category, name)
            for i = 3, 8 do
                local slotId = GetSlotBoundId(i, category)
                if slotId > 0 then
                    local skillName = GetAbilityName(slotId)
                    -- Format: "Crystal Fragments (Front Bar)"
                    table.insert(skills, string.format("%s (%s)", skillName, name))
                end
            end
        end

        -- Scan both bars
        ScanBar(HOTBAR_CATEGORY_PRIMARY, "Front Bar")
        ScanBar(HOTBAR_CATEGORY_BACKUP, "Back Bar")

        return skills
    end

    local function GetUnlockedSkills()
        local list = {}

        -- Iterate through all Skill Types (Class, Weapon, World, Guild, etc.)
        local numSkillTypes = GetNumSkillTypes()

        for skillType = 1, numSkillTypes do
            local numSkillLines = GetNumSkillLines(skillType)

            for skillLineIndex = 1, numSkillLines do
                local lineName, _, _, _, _, _, active = GetSkillLineInfo(skillType, skillLineIndex)

                -- Only check active lines (e.g., don't scan Werewolf if you aren't one)
                if active then
                    local numAbilities = GetNumSkillAbilities(skillType, skillLineIndex)

                    for abilityIndex = 1, numAbilities do
                        local name, _, _, _, _, purchased, _, rank = GetSkillAbilityInfo(skillType, skillLineIndex, abilityIndex)

                        -- CRITICAL FILTER: Only dump if we bought it or have progress
                        if purchased then
                            -- Format: "Destruction Staff: Elemental Blockade (Rank 4)"
                            table.insert(list, string.format("%s: %s (Rank %d)", lineName, name, rank))
                        end
                    end
                end
            end
        end
        return list
    end

    ProxiHUD_Data = {
        timestamp = os.time(),

        -- Lightweight Context (Always loaded)
        name = GetUnitName("player"),
        race = GetUnitRace("player"),
        class = GetUnitClass("player"),
        role = GetSelectedLFGRole(),
        zone = GetUnitZone("player"),
        subzone = GetMapName(),

        -- Stats
        stats = {
            magicka = GetPlayerStat(STAT_MAGICKA_MAX),
            health = GetPlayerStat(STAT_HEALTH_MAX),
            stamina = GetPlayerStat(STAT_STAMINA_MAX)
        },

        -- Currencies
        gold = GetCurrencyAmount(CURT_MONEY, CURRENCY_LOCATION_CHARACTER),
        ap = GetCurrencyAmount(CURT_ALLIANCE_POINTS, CURRENCY_LOCATION_CHARACTER),
        telvar = GetCurrencyAmount(CURT_TELVAR_STONES, CURRENCY_LOCATION_CHARACTER),

        -- HEAVY DATA DUMPS (For AI Tools)
        inventory_dump = GetFullInventory(),
        quest_dump = GetActiveQuests(),
        skills_dump = GetSkills(),
        unlocked_dump = GetUnlockedSkills(), -- Everything you OWN (Passives included)

        -- Legacy field (keep empty to avoid errors if python expects it)
        equipment = {}
    }


    for i = 0, 18 do
        local link = GetItemLink(BAG_WORN, i)
        if link ~= "" then
            table.insert(ProxiHUD_Data.equipment, {
                slot = i,
                name = GetItemLinkName(link),
                link = link
            })
        end
    end
end

EVENT_MANAGER:RegisterForEvent(ProxiHUD.name, EVENT_PLAYER_DEACTIVATED, ProxiHUD.OnPlayerUnloaded)