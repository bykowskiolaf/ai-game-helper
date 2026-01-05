ProxiHUD = {}
ProxiHUD.name = "ProxiHUD_Bridge"

function ProxiHUD.OnPlayerUnloaded()
    local function GetFullInventory()
        local inv = {}

        -- Internal function to scan a specific bag
        local function ScanBag(bagId, locationTag)
            local bagCache = SHARED_INVENTORY:GenerateFullSlotData(nil, bagId)
            for _, data in pairs(bagCache) do
                -- Format: "Iron Sword (x1) [Bank]"
                local entry = data.name
                if data.stackCount > 1 then
                    entry = entry .. " (x" .. data.stackCount .. ")"
                end
                entry = entry .. " [" .. locationTag .. "]"

                table.insert(inv, entry)
            end
        end

        -- Scan both locations
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

    local function GetGoldenPursuits()
        local pursuits = {}

        -- Check if the API exists (Update 44+)
        if not GetActivePromotionalEventId then return pursuits end

        local campaignId = GetActivePromotionalEventId()
        if campaignId == 0 then return pursuits end -- No active campaign

        local numActivities = GetPromotionalEventNumActivities(campaignId)
        for i = 1, numActivities do
            local name, description, _, _, _, _ = GetPromotionalEventActivityInfo(campaignId, i)
            local progress, maxProgress = GetPromotionalEventActivityProgress(campaignId, i)

            -- Format: "Slay Daedra [5/10]: Kill 10 Daedra"
            local entry = string.format("%s [%d/%d]: %s", name, progress, maxProgress, description)
            table.insert(pursuits, entry)
        end
        return pursuits
    end

    local function GetSkills(hotbarCategory)
        local skills = {}
        for i = 3, 8 do
            local slotId = GetSlotBoundId(i, hotbarCategory)
            if slotId > 0 then
                table.insert(skills, GetAbilityName(slotId))
            end
        end
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
        skills_dump = GetSkills(HOTBAR_CATEGORY_PRIMARY),
        golden_pursuits = GetGoldenPursuits(),

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