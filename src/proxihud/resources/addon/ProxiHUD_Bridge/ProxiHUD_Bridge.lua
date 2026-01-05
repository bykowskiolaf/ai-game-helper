ProxiHUD = {}
ProxiHUD.name = "ProxiHUD_Bridge"

function ProxiHUD.OnPlayerUnloaded()
    local function GetFullInventory()
            local inv = {}

            -- Quality Map
            local qualityNames = {[0]="Trash", [1]="Normal", [2]="Fine", [3]="Superior", [4]="Epic", [5]="Legendary"}

            -- Trait Map (Simplified for readability)
            local function GetTraitName(itemLink)
                local traitType, _ = GetItemLinkTraitInfo(itemLink)
                -- You can map specific IDs to strings here, or just use the in-game text
                -- Getting the raw name is easier via GetString("SI_ITEMTRAITTYPE", traitType)
                -- but for simplicity we will just extract it from the link logic if possible
                -- or simpler: use the game's built-in formatter if available,
                -- otherwise just return the ID so the AI can guess or we rely on the item name often containing it.
                -- A better approach for the AI:
                if traitType == 0 then return "None" end
                return GetString("SI_ITEMTRAITTYPE", traitType)
            end

            local function ScanBag(bagId, locationTag)
                local bagCache = SHARED_INVENTORY:GenerateFullSlotData(nil, bagId)

                for _, data in pairs(bagCache) do
                    local link = data.itemLink

                    -- 1. Quality
                    local quality = data.quality or 1
                    local qualityStr = qualityNames[quality] or "Unknown"

                    -- 2. Trait
                    local traitStr = GetTraitName(link)

                    -- 3. Set Name
                    local hasSet, setName, _, _, _ = GetItemLinkSetInfo(link, false)
                    if not hasSet then setName = "No Set" end

                    -- 4. Value
                    local value = GetItemLinkValue(link, false)

                    -- Format: "Mother's Sorrow Inferno Staff (x1) [Bag] {Epic} <Divines> (Set: Mother's Sorrow) $50g"
                    local entry = string.format("%s (x%d) [%s] {%s} <%s> (Set: %s) $%dg",
                        data.name,
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