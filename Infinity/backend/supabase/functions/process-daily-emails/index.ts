import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// Configuration
const BATCH_SIZE = 50;
const VISIBILITY_TIMEOUT = 60;
const MAX_RETRIES = 3;
const QUEUE_NAME = "email_jobs";

// Types
interface EmailJob {
  user_id: string;
  email_type: "morning_planner" | "afternoon_progress" | "eod_summary";
  target_date: string;
  user_email: string;
  user_name: string;
  queued_at: string;
}

interface EmailItems {
  tasks: Array<{
    id: string;
    description: string;
    client_name: string | null;
    due_time: string | null;
    priority: string;
    status: string;
    medium: string | null;
    product_type: string | null;
    carry_forward_count: number;
    original_date: string | null;
    completed_at: string | null;
  }>;
  touchpoints: Array<{
    id: string;
    interaction_type: string;
    purpose: string | null;
    client_name: string | null;
    lead_name: string | null;
    location: string | null;
    scheduled_date: string;
    scheduled_time: string | null;
    status: string;
    completed_at: string | null;
  }>;
  leads: Array<{
    id: string;
    name: string;
    phone: string | null;
    source: string;
    status: string;
    scheduled_time: string | null;
    notes: string | null;
  }>;
  business_opportunities: Array<{
    id: string;
    client_name: string | null;
    lead_name: string | null;
    expected_amount: number | null;
    opportunity_stage: string;
    opportunity_type: string;
    additional_info: string | null;
    due_time: string | null;
    outcome: string;
  }>;
}

// Initialize Supabase client
const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const resendApiKey = Deno.env.get("RESEND_API_KEY")!;
const fromEmail = Deno.env.get("FROM_EMAIL") || "MFD Daily Planner <noreply@yourdomain.com>";

const supabase = createClient(supabaseUrl, supabaseKey);

// Format currency in Indian numbering system
function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return "₹0";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

// Helper to get priority badge color
function getPriorityColor(priority: string): string {
  switch (priority?.toLowerCase()) {
    case "urgent": return "#ef4444";
    case "high": return "#f59e0b";
    case "medium": return "#3b82f6";
    default: return "#9ca3af";
  }
}

// Send email via Resend
async function sendViaResend(
  to: string,
  subject: string,
  html: string
): Promise<{ success: boolean; messageId?: string; error?: string }> {
  try {
    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${resendApiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ from: fromEmail, to: [to], subject, html }),
    });

    const data = await response.json();
    if (response.ok) {
      return { success: true, messageId: data.id };
    }
    return { success: false, error: data.message || "Resend API error" };
  } catch (error) {
    return { success: false, error: String(error) };
  }
}

// Generate Morning Email HTML
function generateMorningEmail(job: EmailJob, items: EmailItems): string {
  const totalItems =
    items.tasks.length +
    items.touchpoints.length +
    items.leads.length +
    items.business_opportunities.length;
  const carryForwardedTasks = items.tasks.filter((t) => t.carry_forward_count > 0);

  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          
          <!-- Header -->
          <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 32px 24px; text-align: center; color: white;">
            <h1 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 700;">☀️ Good Morning, ${job.user_name}!</h1>
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">${new Date(job.target_date).toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</p>
          </div>

          <!-- Summary Cards -->
          <div style="padding: 24px; background-color: #f9fafb;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
              <tr>
                <td width="50%" style="padding: 6px;">
                  <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #3b82f6; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #1f2937;">${items.tasks.length}</div>
                    <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">Tasks</div>
                  </div>
                </td>
                <td width="50%" style="padding: 6px;">
                  <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #10b981; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #1f2937;">${items.touchpoints.length}</div>
                    <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">Touchpoints</div>
                  </div>
                </td>
              </tr>
              <tr>
                <td width="50%" style="padding: 6px;">
                  <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #f59e0b; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #1f2937;">${items.leads.length}</div>
                    <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">Leads</div>
                  </div>
                </td>
                <td width="50%" style="padding: 6px;">
                  <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #8b5cf6; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #1f2937;">${items.business_opportunities.length}</div>
                    <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">Opportunities</div>
                  </div>
                </td>
              </tr>
            </table>
          </div>

          <!-- Content -->
          <div style="padding: 24px;">
            
            ${carryForwardedTasks.length > 0 ? `
              <div style="margin-bottom: 24px;">
                <h2 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: #1f2937;">⚠️ Carry-forwarded Tasks</h2>
                ${carryForwardedTasks.map((t) => `
                  <div style="background-color: #fffbeb; padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #f59e0b;">
                    <div style="font-weight: 500; color: #1f2937; margin-bottom: 4px;">${t.description}</div>
                    ${t.client_name ? `<div style="font-size: 12px; color: #6b7280;">👤 ${t.client_name}</div>` : ""}
                    <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">🔄 Carried forward ${t.carry_forward_count} time${t.carry_forward_count > 1 ? "s" : ""} from ${new Date(t.original_date!).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}</div>
                    <span style="display: inline-block; background-color: ${getPriorityColor(t.priority)}; color: white; font-size: 11px; font-weight: 600; padding: 2px 6px; border-radius: 3px; margin-top: 6px;">${t.priority?.toUpperCase()}</span>
                  </div>
                `).join("")}
              </div>
            ` : ""}

            ${items.tasks.filter((t) => t.carry_forward_count === 0).length > 0 ? `
              <div style="margin-bottom: 24px;">
                <h2 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: #1f2937;">📋 Today's Tasks</h2>
                ${items.tasks.filter((t) => t.carry_forward_count === 0).map((t) => `
                  <div style="background-color: #f9fafb; padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid ${getPriorityColor(t.priority)};">
                    <div style="font-weight: 500; color: #1f2937; margin-bottom: 4px;">${t.description}</div>
                    <div style="font-size: 12px; color: #6b7280;">
                      ${t.client_name ? `👤 ${t.client_name} • ` : ""}${t.due_time ? `🕐 ${t.due_time}` : ""}${t.medium ? ` • ${t.medium}` : ""}
                    </div>
                    ${t.product_type ? `<div style="font-size: 12px; color: #6b7280; margin-top: 4px;">📦 ${t.product_type}</div>` : ""}
                  </div>
                `).join("")}
              </div>
            ` : ""}

            ${items.touchpoints.length > 0 ? `
              <div style="margin-bottom: 24px;">
                <h2 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: #1f2937;">📞 Scheduled Touchpoints</h2>
                ${items.touchpoints.map((tp) => `
                  <div style="background-color: #f9fafb; padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #10b981;">
                    <div style="font-weight: 500; color: #1f2937; margin-bottom: 4px;">${tp.interaction_type}</div>
                    <div style="font-size: 12px; color: #6b7280;">
                      ${tp.client_name ? `👤 ${tp.client_name}` : ""}${tp.lead_name ? `👤 ${tp.lead_name}` : ""}${tp.scheduled_time ? ` • 🕐 ${tp.scheduled_time}` : ""}${tp.location ? ` • 📍 ${tp.location}` : ""}
                    </div>
                    ${tp.purpose ? `<div style="font-size: 12px; color: #6b7280; margin-top: 4px;">💬 ${tp.purpose}</div>` : ""}
                  </div>
                `).join("")}
              </div>
            ` : ""}

            ${items.leads.length > 0 ? `
              <div style="margin-bottom: 24px;">
                <h2 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: #1f2937;">🎯 Lead Follow-ups</h2>
                ${items.leads.map((l) => `
                  <div style="background-color: #f9fafb; padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #f59e0b;">
                    <div style="font-weight: 500; color: #1f2937; margin-bottom: 4px;">${l.name}</div>
                    <div style="font-size: 12px; color: #6b7280;">
                      ${l.source ? `📌 ${l.source} • ` : ""}${l.status || "Follow-up"}${l.scheduled_time ? ` • 🕐 ${l.scheduled_time}` : ""}
                    </div>
                    ${l.phone ? `<div style="font-size: 12px; color: #6b7280; margin-top: 4px;">📱 ${l.phone}</div>` : ""}
                  </div>
                `).join("")}
              </div>
            ` : ""}

            ${items.business_opportunities.length > 0 ? `
              <div style="margin-bottom: 24px;">
                <h2 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: #1f2937;">💼 Business Opportunities</h2>
                ${items.business_opportunities.map((bo) => `
                  <div style="background-color: #f9fafb; padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #8b5cf6;">
                    <div style="font-weight: 500; color: #1f2937; margin-bottom: 4px;">${bo.client_name || bo.lead_name || "Opportunity"}</div>
                    <div style="font-size: 12px; color: #6b7280;">
                      💰 ${formatCurrency(bo.expected_amount)} • 📊 ${bo.opportunity_stage} • 🏷️ ${bo.opportunity_type}
                    </div>
                    ${bo.additional_info ? `<div style="font-size: 12px; color: #6b7280; margin-top: 4px;">📝 ${bo.additional_info}</div>` : ""}
                  </div>
                `).join("")}
              </div>
            ` : ""}

            ${totalItems === 0 ? `
              <div style="text-align: center; padding: 32px 24px; color: #6b7280;">
                <div style="font-size: 24px; margin-bottom: 8px;">🎉</div>
                <p style="margin: 0; font-weight: 500;">No items scheduled for today!</p>
                <p style="margin: 8px 0 0 0; font-size: 14px;">Enjoy your morning!</p>
              </div>
            ` : ""}

          </div>

          <!-- Footer -->
          <div style="background-color: #f9fafb; padding: 24px; text-align: center; border-top: 1px solid #e5e7eb;">
            <p style="margin: 0; font-size: 14px; color: #6b7280;">Have a productive day! 🚀</p>
          </div>

        </div>
      </body>
    </html>
  `;
}

// Generate Midday Email HTML
function generateMiddayEmail(job: EmailJob, items: EmailItems): string {
  const completedTasks = items.tasks.filter((t) => t.status === "completed");
  const completedTouchpoints = items.touchpoints.filter((tp) => tp.status === "completed");
  const completedLeads = items.leads.filter((l) => l.status === "converted");
  const completedOpportunities = items.business_opportunities.filter((o) => o.outcome !== "open");

  const totalCompleted = completedTasks.length + completedTouchpoints.length + completedLeads.length + completedOpportunities.length;
  const totalItems = items.tasks.length + items.touchpoints.length + items.leads.length + items.business_opportunities.length;
  const completedPercent = totalItems > 0 ? Math.round((totalCompleted / totalItems) * 100) : 0;

  const pendingTasks = items.tasks.filter((t) => t.status !== "completed");
  const pendingTouchpoints = items.touchpoints.filter((tp) => tp.status !== "completed");
  const pendingLeads = items.leads.filter((l) => l.status !== "converted");
  const pendingOpportunities = items.business_opportunities.filter((o) => o.outcome === "open");

  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          
          <!-- Header -->
          <div style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); padding: 32px 24px; text-align: center; color: white;">
            <h1 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 700;">⏰ Midday Check</h1>
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">${new Date(job.target_date).toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</p>
          </div>

          <!-- Progress Section -->
          <div style="padding: 32px 24px; background-color: #f9fafb; text-align: center;">
            <div style="background: white; padding: 24px; border-radius: 8px;">
              <div style="font-size: 48px; font-weight: 700; color: #ea580c;">${completedPercent}%</div>
              <div style="font-size: 14px; color: #6b7280; margin-top: 8px;">Complete (${totalCompleted}/${totalItems})</div>
              <div style="background: #e5e7eb; height: 8px; border-radius: 4px; margin: 16px 0; overflow: hidden;">
                <div style="background: #22c55e; height: 100%; width: ${completedPercent}%; border-radius: 4px;"></div>
              </div>
            </div>
          </div>

          <!-- Stats Row -->
          <div style="padding: 0 24px 24px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
              <tr>
                <td width="50%" style="padding: 6px;">
                  <div style="background-color: #d1fae5; padding: 16px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 20px; font-weight: 700; color: #065f46;">${totalCompleted}</div>
                    <div style="font-size: 12px; color: #047857; margin-top: 4px;">✅ Completed</div>
                  </div>
                </td>
                <td width="50%" style="padding: 6px;">
                  <div style="background-color: #fee2e2; padding: 16px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 20px; font-weight: 700; color: #7f1d1d;">${totalItems - totalCompleted}</div>
                    <div style="font-size: 12px; color: #dc2626; margin-top: 4px;">🔥 Pending</div>
                  </div>
                </td>
              </tr>
            </table>
          </div>

          <!-- Content -->
          <div style="padding: 0 24px 24px 24px;">

            <!-- Completed Items -->
            <div style="margin-bottom: 24px;">
              <h2 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: #1f2937;">✅ Completed Items</h2>
              ${completedTasks.map((t) => `
                <div style="background-color: #d1fae5; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 13px; color: #047857;">
                  ✓ ${t.description}${t.client_name ? ` (${t.client_name})` : ""}
                </div>
              `).join("")}
              ${completedTouchpoints.map((tp) => `
                <div style="background-color: #d1fae5; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 13px; color: #047857;">
                  ✓ ${tp.interaction_type}${tp.client_name || tp.lead_name ? ` (${tp.client_name || tp.lead_name})` : ""}
                </div>
              `).join("")}
              ${completedLeads.map((l) => `
                <div style="background-color: #d1fae5; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 13px; color: #047857;">
                  ✓ Lead: ${l.name} (converted)
                </div>
              `).join("")}
              ${completedOpportunities.map((o) => `
                <div style="background-color: #d1fae5; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 13px; color: #047857;">
                  ✓ ${o.client_name || o.lead_name || "Opportunity"} (${o.outcome})
                </div>
              `).join("")}
              ${totalCompleted === 0 ? `
                <div style="background-color: #f3f4f6; padding: 12px; border-radius: 6px; text-align: center; color: #6b7280; font-size: 13px;">
                  No completed items yet. Keep working! 💪
                </div>
              ` : ""}
            </div>

            <!-- Pending Items -->
            <div>
              <h2 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: #1f2937;">🔥 Still Pending</h2>
              ${pendingTasks.length > 0 ? `
                <div style="margin-bottom: 12px;">
                  <div style="font-size: 13px; font-weight: 500; color: #6b7280; margin-bottom: 6px;">Tasks</div>
                  ${pendingTasks.map((t) => `
                    <div style="background-color: #fef3c7; padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; font-size: 13px; color: #92400e; border-left: 3px solid ${getPriorityColor(t.priority)};">
                      • ${t.description}${t.client_name ? ` (${t.client_name})` : ""}
                    </div>
                  `).join("")}
                </div>
              ` : ""}
              ${pendingTouchpoints.length > 0 ? `
                <div style="margin-bottom: 12px;">
                  <div style="font-size: 13px; font-weight: 500; color: #6b7280; margin-bottom: 6px;">Touchpoints</div>
                  ${pendingTouchpoints.map((tp) => `
                    <div style="background-color: #fef3c7; padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; font-size: 13px; color: #92400e;">
                      • ${tp.interaction_type}${tp.client_name || tp.lead_name ? ` (${tp.client_name || tp.lead_name})` : ""}
                    </div>
                  `).join("")}
                </div>
              ` : ""}
              ${pendingLeads.length > 0 ? `
                <div style="margin-bottom: 12px;">
                  <div style="font-size: 13px; font-weight: 500; color: #6b7280; margin-bottom: 6px;">Leads</div>
                  ${pendingLeads.map((l) => `
                    <div style="background-color: #fef3c7; padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; font-size: 13px; color: #92400e;">
                      • ${l.name} (${l.status})
                    </div>
                  `).join("")}
                </div>
              ` : ""}
              ${pendingOpportunities.length > 0 ? `
                <div style="margin-bottom: 12px;">
                  <div style="font-size: 13px; font-weight: 500; color: #6b7280; margin-bottom: 6px;">Opportunities</div>
                  ${pendingOpportunities.map((o) => `
                    <div style="background-color: #fef3c7; padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; font-size: 13px; color: #92400e;">
                      • ${o.client_name || o.lead_name || "Opportunity"} (${formatCurrency(o.expected_amount)})
                    </div>
                  `).join("")}
                </div>
              ` : ""}
              ${totalItems - totalCompleted === 0 ? `
                <div style="background-color: #d1fae5; padding: 12px; border-radius: 6px; text-align: center; color: #047857; font-size: 13px; font-weight: 500;">
                  🎉 All items complete! Great work!
                </div>
              ` : ""}
            </div>

          </div>

          <!-- Footer -->
          <div style="background-color: #f9fafb; padding: 24px; text-align: center; border-top: 1px solid #e5e7eb;">
            <p style="margin: 0; font-size: 14px; color: #6b7280;">Keep going, ${job.user_name}! 💪</p>
          </div>

        </div>
      </body>
    </html>
  `;
}

// Generate EOD Email HTML
function generateEodEmail(job: EmailJob, items: EmailItems): string {
  const completedTasks = items.tasks.filter((t) => t.status === "completed");
  const completedTouchpoints = items.touchpoints.filter((tp) => tp.status === "completed");
  const completedLeads = items.leads.filter((l) => l.status === "converted");
  const completedOpportunities = items.business_opportunities.filter((o) => o.outcome !== "open");

  const totalCompleted = completedTasks.length + completedTouchpoints.length + completedLeads.length + completedOpportunities.length;

  const pendingTasks = items.tasks.filter((t) => t.status !== "completed");
  const pendingTouchpoints = items.touchpoints.filter((tp) => tp.status !== "completed");
  const pendingLeads = items.leads.filter((l) => l.status !== "converted");
  const pendingOpportunities = items.business_opportunities.filter((o) => o.outcome === "open");

  const totalPending = pendingTasks.length + pendingTouchpoints.length + pendingLeads.length + pendingOpportunities.length;

  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          
          <!-- Header -->
          <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 32px 24px; text-align: center; color: white;">
            <h1 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 700;">🌙 End of Day Summary</h1>
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">${new Date(job.target_date).toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</p>
          </div>

          <!-- Score Card -->
          <div style="padding: 32px 24px; background-color: #f9fafb; text-align: center;">
            <div style="background: white; padding: 24px; border-radius: 8px; border: 2px solid #22c55e;">
              <div style="font-size: 48px; font-weight: 700; color: #22c55e;">${totalCompleted}</div>
              <div style="font-size: 16px; color: #1f2937; margin-top: 8px; font-weight: 600;">Items Completed Today 🎉</div>
            </div>
          </div>

          <!-- Two Column Layout -->
          <div style="padding: 24px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
              <tr>
                <td width="50%" style="padding: 8px; vertical-align: top;">
                  <div style="background-color: #f0fdf4; padding: 16px; border-radius: 8px; border-left: 4px solid #22c55e;">
                    <h3 style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600; color: #15803d;">✅ Completed</h3>
                    ${completedTasks.map((t) => `
                      <div style="font-size: 12px; color: #15803d; margin-bottom: 4px;">• ${t.description}${t.client_name ? ` (${t.client_name})` : ""}</div>
                    `).join("")}
                    ${completedTouchpoints.map((tp) => `
                      <div style="font-size: 12px; color: #15803d; margin-bottom: 4px;">• ${tp.interaction_type}${tp.client_name || tp.lead_name ? ` (${tp.client_name || tp.lead_name})` : ""}</div>
                    `).join("")}
                    ${completedLeads.map((l) => `
                      <div style="font-size: 12px; color: #15803d; margin-bottom: 4px;">• ${l.name} (Converted)</div>
                    `).join("")}
                    ${completedOpportunities.map((o) => `
                      <div style="font-size: 12px; color: #15803d; margin-bottom: 4px;">• ${o.client_name || o.lead_name || "Opportunity"}</div>
                    `).join("")}
                    ${totalCompleted === 0 ? `<div style="font-size: 12px; color: #6b7280;">No completed items</div>` : ""}
                  </div>
                </td>
                <td width="50%" style="padding: 8px; vertical-align: top;">
                  <div style="background-color: #fffbeb; padding: 16px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                    <h3 style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600; color: #b45309;">📅 Carry Forward</h3>
                    ${pendingTasks.map((t) => `
                      <div style="font-size: 12px; color: #92400e; margin-bottom: 4px;">• ${t.description}${t.client_name ? ` (${t.client_name})` : ""}</div>
                    `).join("")}
                    ${pendingTouchpoints.map((tp) => `
                      <div style="font-size: 12px; color: #92400e; margin-bottom: 4px;">• ${tp.interaction_type}${tp.client_name || tp.lead_name ? ` (${tp.client_name || tp.lead_name})` : ""}</div>
                    `).join("")}
                    ${pendingLeads.map((l) => `
                      <div style="font-size: 12px; color: #92400e; margin-bottom: 4px;">• Lead: ${l.name}</div>
                    `).join("")}
                    ${pendingOpportunities.map((o) => `
                      <div style="font-size: 12px; color: #92400e; margin-bottom: 4px;">• ${o.client_name || o.lead_name || "Opportunity"}</div>
                    `).join("")}
                    ${totalPending === 0 ? `<div style="font-size: 12px; color: #6b7280;">Nothing to carry forward!</div>` : ""}
                  </div>
                </td>
              </tr>
            </table>
          </div>

          <!-- Footer -->
          <div style="background-color: #f9fafb; padding: 24px; text-align: center; border-top: 1px solid #e5e7eb;">
            <p style="margin: 0; font-size: 14px; color: #6b7280;">Great work, ${job.user_name}! Rest well. 💤</p>
          </div>

        </div>
      </body>
    </html>
  `;
}

// Generate email based on type
function generateEmail(job: EmailJob, items: EmailItems): { subject: string; html: string } {
  if (job.email_type === "morning_planner") {
    const totalItems = items.tasks.length + items.touchpoints.length + items.leads.length + items.business_opportunities.length;
    return {
      subject: `☀️ Good Morning ${job.user_name}! ${totalItems} items planned for today`,
      html: generateMorningEmail(job, items),
    };
  }

  if (job.email_type === "afternoon_progress") {
    const totalItems = items.tasks.length + items.touchpoints.length + items.leads.length + items.business_opportunities.length;
    const completed =
      items.tasks.filter((t) => t.status === "completed").length +
      items.touchpoints.filter((tp) => tp.status === "completed").length +
      items.leads.filter((l) => l.status === "converted").length +
      items.business_opportunities.filter((o) => o.outcome !== "open").length;
    const pct = totalItems > 0 ? Math.round((completed / totalItems) * 100) : 0;

    return {
      subject: `⏰ Midday Check: ${pct}% done (${completed}/${totalItems})`,
      html: generateMiddayEmail(job, items),
    };
  }

  if (job.email_type === "eod_summary") {
    const completed =
      items.tasks.filter((t) => t.status === "completed").length +
      items.touchpoints.filter((tp) => tp.status === "completed").length +
      items.leads.filter((l) => l.status === "converted").length +
      items.business_opportunities.filter((o) => o.outcome !== "open").length;

    const pending =
      items.tasks.filter((t) => t.status !== "completed").length +
      items.touchpoints.filter((tp) => tp.status !== "completed").length +
      items.leads.filter((l) => l.status !== "converted").length +
      items.business_opportunities.filter((o) => o.outcome === "open").length;

    return {
      subject: `🌙 Day Complete: ${completed} done, ${pending} to carry forward`,
      html: generateEodEmail(job, items),
    };
  }

  return { subject: "Daily Update", html: "<p>Invalid email type</p>" };
}

// STEP 1: Schedule emails
async function scheduleEmails(): Promise<number> {
  const emailTypes = [
    { rpc: "get_users_for_morning_email", type: "morning_planner" },
    { rpc: "get_users_for_afternoon_email", type: "afternoon_progress" },
    { rpc: "get_users_for_eod_email", type: "eod_summary" },
  ];

  let queuedCount = 0;

  for (const et of emailTypes) {
    const { data: users, error } = await supabase.rpc(et.rpc, { window_minutes: 15 });

    if (error) {
      console.error(`Error fetching users for ${et.type}:`, error);
      continue;
    }

    for (const user of users || []) {
      // Get IST date using deterministic UTC offset (5.5 hours ahead)
      const now = new Date();
      const istOffsetMs = 5.5 * 60 * 60 * 1000;
      const istNow = new Date(now.getTime() + istOffsetMs);
      const istDate = istNow.toISOString().split("T")[0];

      const { error: queueError } = await supabase.rpc("queue_email_job", {
        p_user_id: user.user_id,
        p_email_type: et.type,
        p_target_date: istDate,
        p_user_email: user.user_email,
        p_user_name: user.user_name,
      });

      if (queueError) {
        console.error(`Error queuing email for ${user.user_id}:`, queueError);
      } else {
        queuedCount++;
      }
    }
  }

  console.log(`Scheduled ${queuedCount} emails`);
  return queuedCount;
}

// STEP 2: Process emails
async function processEmails(): Promise<number> {
  const { data: messages, error } = await supabase.rpc("pgmq_read", {
    p_queue_name: QUEUE_NAME,
    p_vt: VISIBILITY_TIMEOUT,
    p_qty: BATCH_SIZE,
  });

  if (error) {
    console.error("Error reading from queue:", error);
    return 0;
  }

  let sentCount = 0;

  for (const msg of messages || []) {
    const job: EmailJob = msg.message;
    const msgId: number = msg.msg_id;
    const readCt: number = msg.read_ct;

    try {
      // 1. Dedup check
      const { data: existing } = await supabase
        .from("email_logs")
        .select("id")
        .eq("user_id", job.user_id)
        .eq("email_type", job.email_type)
        .eq("target_date", job.target_date)
        .eq("status", "sent")
        .maybeSingle();

      if (existing) {
        console.log(`Email already sent for ${job.user_id} / ${job.email_type}`);
        await supabase.rpc("pgmq_delete", { p_queue_name: QUEUE_NAME, p_msg_id: msgId });
        continue;
      }

      // 2. Fetch fresh data
      const { data: items, error: itemsError } = await supabase.rpc("get_email_daily_items", {
        p_user_id: job.user_id,
        p_date: job.target_date,
      });

      if (itemsError) {
        throw new Error(`Failed to fetch items: ${itemsError.message}`);
      }

      const emailItems: EmailItems = items || {
        tasks: [],
        touchpoints: [],
        leads: [],
        business_opportunities: [],
      };

      // 3. Generate email
      const { subject, html } = generateEmail(job, emailItems);

      // 4. Send via Resend
      const result = await sendViaResend(job.user_email, subject, html);

      // 5a. On success
      if (result.success) {
        await supabase.from("email_logs").insert({
          user_id: job.user_id,
          email_type: job.email_type,
          target_date: job.target_date,
          recipient_email: job.user_email,
          subject,
          status: "sent",
          resend_message_id: result.messageId,
          items_snapshot: emailItems,
        });

        await supabase.rpc("pgmq_delete", { p_queue_name: QUEUE_NAME, p_msg_id: msgId });
        sentCount++;
        console.log(`Email sent to ${job.user_email} (${job.email_type})`);
      } else {
        // 5b. On failure
        if (readCt >= MAX_RETRIES) {
          await supabase.rpc("move_to_dlq", {
            p_msg_id: msgId,
            p_message: job,
            p_error: result.error || "Unknown error",
          });
          await supabase.rpc("pgmq_delete", { p_queue_name: QUEUE_NAME, p_msg_id: msgId });
          console.log(`Message moved to DLQ after ${MAX_RETRIES} retries`);
        } else {
          console.log(`Email send failed for ${job.user_email}, will retry (attempt ${readCt + 1})`);
        }

        // Log failure
        await supabase.from("email_logs").insert({
          user_id: job.user_id,
          email_type: job.email_type,
          target_date: job.target_date,
          recipient_email: job.user_email,
          status: "failed",
          error_message: result.error || "Unknown error",
        });
      }
    } catch (error) {
      console.error(`Error processing message ${msgId}:`, error);

      if (readCt >= MAX_RETRIES) {
        await supabase.rpc("move_to_dlq", {
          p_msg_id: msgId,
          p_message: job,
          p_error: String(error),
        });
        await supabase.rpc("pgmq_delete", { p_queue_name: QUEUE_NAME, p_msg_id: msgId });
      }
    }
  }

  console.log(`Processed and sent ${sentCount} emails`);
  return sentCount;
}

// Main handler
Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    console.log("Starting email service...");

    const scheduledCount = await scheduleEmails();
    const sentCount = await processEmails();

    return new Response(
      JSON.stringify({ success: true, scheduled: scheduledCount, sent: sentCount }),
      { headers: { "Content-Type": "application/json" }, status: 200 }
    );
  } catch (error) {
    console.error("Error in email service:", error);
    return new Response(
      JSON.stringify({ success: false, error: String(error) }),
      { headers: { "Content-Type": "application/json" }, status: 500 }
    );
  }
});